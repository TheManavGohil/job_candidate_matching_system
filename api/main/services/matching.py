"""
Core matching engine – section-wise semantic similarity with Reciprocal Rank Fusion.
Implements the algorithm from spec §7.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import numpy as np

from main.services.qdrant_client import (
    get_candidate_section_vector,
    get_jd_section_vectors,
    search_candidates_by_section,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  Section mapping: JD section → candidate section(s)
# ═══════════════════════════════════════════════════════════════

DEFAULT_SECTION_MAP = {
    "required_skills": ["skills"],
    "preferred_skills": ["skills"],
    "responsibilities": ["experience", "projects"],
    "qualifications": ["education", "experience"],
    "context": ["experience"],
}

DEFAULT_WEIGHTS = {
    "required_skills": 30.0,
    "preferred_skills": 10.0,
    "responsibilities": 25.0,
    "qualifications": 20.0,
    "context": 15.0,
}

RRF_K = 60  # Reciprocal rank fusion constant


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity, clipping negatives to 0."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    sim = float(np.dot(va, vb) / denom)
    return max(sim, 0.0)  # Clip negatives


def years_match_score(candidate_years: float, jd_min_years: float) -> float:
    """Piecewise years matching: 1.0 if enough, proportional otherwise."""
    if jd_min_years <= 0:
        return 1.0
    if candidate_years >= jd_min_years:
        return 1.0
    return candidate_years / jd_min_years


# ═══════════════════════════════════════════════════════════════
#  Main matching pipeline
# ═══════════════════════════════════════════════════════════════

def compute_matches(
    jd_id: str,
    company_id: str,
    jd_json: dict[str, Any],
    weights: dict[str, float],
    top_k: int = 200,
    retrieval_k: int = 500,
) -> list[dict[str, Any]]:
    """
    Full matching pipeline:
    1. Get JD section vectors from Qdrant
    2. Per-section candidate search
    3. Reciprocal Rank Fusion
    4. Final weighted scoring
    """
    # Normalise weights
    total_w = sum(weights.values()) or 1
    norm_weights = {k: v / total_w * 100 for k, v in weights.items()}

    # Step 1: Get JD vectors
    jd_vectors = get_jd_section_vectors(jd_id)
    if not jd_vectors:
        logger.warning(f"No JD vectors found for {jd_id}")
        return []

    # Step 2: Per-section search + RRF
    candidate_ranks: dict[str, dict[str, int]] = defaultdict(dict)  # candidate_id -> {section: rank}
    candidate_section_scores: dict[str, dict[str, float]] = defaultdict(dict)

    for jd_section, jd_vector in jd_vectors.items():
        cand_sections = DEFAULT_SECTION_MAP.get(jd_section, ["skills"])

        for cand_section in cand_sections:
            results = search_candidates_by_section(
                section_vector=jd_vector,
                section_name=cand_section,
                company_id=company_id,
                top_k=retrieval_k,
            )

            for rank, hit in enumerate(results):
                cid = hit["candidate_id"]
                score = hit["score"]
                section_key = f"{jd_section}_vs_{cand_section}"

                # Keep best rank per JD section for this candidate
                existing_rank = candidate_ranks.get(cid, {}).get(jd_section, float("inf"))
                if rank < existing_rank:
                    candidate_ranks[cid][jd_section] = rank

                # Keep best score per JD section
                existing_score = candidate_section_scores.get(cid, {}).get(jd_section, 0.0)
                candidate_section_scores[cid][jd_section] = max(existing_score, score)

    if not candidate_ranks:
        logger.info("No candidates found in vector search")
        return []

    # Step 3: RRF scoring to get shortlist
    rrf_scores: dict[str, float] = {}
    for cid, section_ranks in candidate_ranks.items():
        rrf = sum(1.0 / (RRF_K + rank) for rank in section_ranks.values())
        rrf_scores[cid] = rrf

    # Sort by RRF and keep top candidates
    sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    shortlist = [cid for cid, _ in sorted_candidates[:top_k * 2]]

    # Step 4: Final weighted scoring
    jd_qualifications = jd_json.get("qualifications", {})
    jd_min_years = jd_qualifications.get("min_years", 0) if isinstance(jd_qualifications, dict) else 0

    results = []
    for cid in shortlist:
        section_scores = candidate_section_scores.get(cid, {})
        total_score = 0.0

        for jd_section, weight in norm_weights.items():
            sim = section_scores.get(jd_section, 0.0)

            # Special handling for qualifications: composite score
            if jd_section == "qualifications":
                edu_sim = sim  # Already the best from education/experience search
                # We'd need candidate total_years for years_match,
                # but it's stored in DB; for now use the vector similarity
                composite = edu_sim
                total_score += weight * composite
            elif jd_section == "responsibilities":
                # Already took max across experience + projects
                total_score += weight * sim
            else:
                total_score += weight * sim

        # Normalise to 0-100 scale
        final_score = round(total_score, 2)

        results.append({
            "candidate_id": cid,
            "total_score": final_score,
            "section_scores": {k: round(v, 4) for k, v in section_scores.items()},
        })

    # Sort by total score descending
    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results[:top_k]
