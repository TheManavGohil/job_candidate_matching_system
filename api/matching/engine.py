"""
Matching engine — computes multi-facet scores between a JD and a candidate.
"""

import logging
import re
from typing import Dict, Any, List, Optional

import numpy as np

from api.matching.weights import WEIGHTS, get_label
from api.preprocessing.embeddings import (
    compute_embedding, compute_skills_embedding, cosine_similarity,
)

logger = logging.getLogger(__name__)

DEGREE_LEVELS = {"associate": 1, "diploma": 1, "bachelor": 2, "master": 3, "phd": 4}


def _get_degree_level(text: Optional[str]) -> int:
    """Extract degree level from text. Returns 0 if unknown."""
    if not text:
        return 0
    t = text.lower()
    best = 0
    for kw, level in DEGREE_LEVELS.items():
        if kw in t:
            best = max(best, level)
    return best


def _extract_required_degree(jd_text: str) -> int:
    """Extract required degree level from JD text."""
    t = jd_text.lower()
    # Check for explicit degree requirements
    patterns = [
        (r"(?:phd|ph\.d|doctorate)", 4),
        (r"(?:master|m\.s\.|m\.sc|mba|m\.tech)", 3),
        (r"(?:bachelor|b\.s\.|b\.sc|b\.tech|b\.e\.)", 2),
    ]
    for pat, level in patterns:
        if re.search(pat, t):
            return level
    return 0


def compute_skill_match(jd: Dict, candidate: Dict) -> Dict[str, Any]:
    """
    Compute skill match score (0-100).

    Components:
    - Exact overlap (Jaccard-like) for required and preferred skills
    - Semantic similarity between skill embeddings
    """
    required = set(s.lower() for s in (jd.get("required_skills") or []))
    preferred = set(s.lower() for s in (jd.get("preferred_skills") or []))
    cand_skills = set(s.lower() for s in (candidate.get("skills") or []))

    # Exact overlap
    matched_req = cand_skills & required
    matched_pref = cand_skills & preferred
    missing_req = required - cand_skills

    j_req = len(matched_req) / max(len(required), 1)
    j_pref = len(matched_pref) / max(len(preferred), 1) if preferred else 1.0
    exact_score = 0.7 * j_req + 0.3 * j_pref

    # Semantic similarity
    jd_skill_emb = jd.get("embedding_skills")
    cand_skill_emb = candidate.get("embedding_skills")

    if jd_skill_emb is None and required:
        jd_skill_emb = compute_skills_embedding(list(required))
    elif jd_skill_emb is None:
        jd_skill_emb = jd.get("embedding_summary")

    sem_score = 0.5
    if jd_skill_emb is not None and cand_skill_emb is not None:
        cos_sim = cosine_similarity(jd_skill_emb, cand_skill_emb)
        sem_score = (cos_sim + 1) / 2

    skill_score = (0.5 * exact_score + 0.5 * sem_score) * 100

    return {
        "score": round(min(100, max(0, skill_score)), 2),
        "matched_required": sorted(matched_req),
        "matched_preferred": sorted(matched_pref),
        "missing_required": sorted(missing_req),
        "extra_skills": sorted(cand_skills - required - preferred),
        "exact_score": round(exact_score, 3),
        "semantic_score": round(sem_score, 3),
    }


def compute_experience_match(jd: Dict, candidate: Dict) -> Dict[str, Any]:
    """
    Compute experience match score (0-100).

    Components: years score, role alignment, domain relevance.
    """
    # Years score
    M = jd.get("min_years") or 0
    Y = candidate.get("years_of_experience") or 0
    if M == 0 and Y == 0:
        years_score = 1.0
    elif M == 0:
        years_score = 1.0
    elif Y >= M:
        years_score = min(1.0, Y / max(1, M))
    else:
        years_score = Y / max(1, M)

    # Role alignment
    role_score = 0.5
    jd_title = jd.get("role_type") or jd.get("title") or ""
    cand_title = candidate.get("current_title") or ""
    if jd_title and cand_title:
        try:
            jd_title_emb = compute_embedding(jd_title)
            cand_title_emb = compute_embedding(cand_title)
            sim = cosine_similarity(jd_title_emb, cand_title_emb)
            role_score = (sim + 1) / 2
        except Exception:
            role_score = 0.5

    # Domain relevance
    domain_score = 0.5
    jd_summary_emb = jd.get("embedding_summary")
    cand_summary_emb = candidate.get("embedding_summary")
    if jd_summary_emb is not None and cand_summary_emb is not None:
        sim = cosine_similarity(jd_summary_emb, cand_summary_emb)
        domain_score = (sim + 1) / 2

    exp_score = (0.5 * years_score + 0.3 * role_score + 0.2 * domain_score) * 100

    return {
        "score": round(min(100, max(0, exp_score)), 2),
        "years_score": round(years_score, 3),
        "role_score": round(role_score, 3),
        "domain_score": round(domain_score, 3),
        "candidate_years": Y,
        "required_years": M,
    }


def compute_education_match(jd: Dict, candidate: Dict) -> Dict[str, Any]:
    """Compute education match score (0-100)."""
    jd_text = jd.get("raw_text", "") + " " + (jd.get("core_requirements_text") or "")
    req_level = _extract_required_degree(jd_text)
    cand_level = _get_degree_level(candidate.get("education"))

    req_name = {0: "None", 1: "Associate", 2: "Bachelor", 3: "Master", 4: "PhD"}.get(req_level, "None")
    cand_name = {0: "Unknown", 1: "Associate", 2: "Bachelor", 3: "Master", 4: "PhD"}.get(cand_level, "Unknown")

    if req_level == 0:
        score = 100.0
    elif cand_level >= req_level:
        score = 100.0
    elif cand_level == req_level - 1:
        score = 50.0
    else:
        score = 20.0

    return {
        "score": score,
        "required_level": req_name,
        "candidate_level": cand_name,
    }


def compute_contextual_fit(jd: Dict, candidate: Dict) -> Dict[str, Any]:
    """Compute contextual fit score (0-100) via embedding similarity."""
    jd_emb = jd.get("embedding_summary") if jd.get("embedding_summary") is not None else jd.get("embedding_skills")
    cand_emb = candidate.get("embedding_summary") if candidate.get("embedding_summary") is not None else candidate.get("embedding_skills")

    if jd_emb is not None and cand_emb is not None:
        sim = cosine_similarity(jd_emb, cand_emb)
        score = (sim + 1) * 50
    else:
        score = 50.0

    return {"score": round(min(100, max(0, score)), 2)}


def compute_match(jd: Dict, candidate: Dict) -> Dict[str, Any]:
    """
    Full matching pipeline: compute all facets, apply weights and penalties.

    Args:
        jd: job description dict (from get_job_dict)
        candidate: candidate dict (from get_candidate_dict)

    Returns:
        Complete match result with scores, details, and label.
    """
    skill_result = compute_skill_match(jd, candidate)
    exp_result = compute_experience_match(jd, candidate)
    edu_result = compute_education_match(jd, candidate)
    ctx_result = compute_contextual_fit(jd, candidate)

    # Weighted total
    total = (
        WEIGHTS["skill_match"] * skill_result["score"]
        + WEIGHTS["experience_match"] * exp_result["score"]
        + WEIGHTS["education_match"] * edu_result["score"]
        + WEIGHTS["contextual_fit"] * ctx_result["score"]
    )

    # Critical skill penalty
    missing_count = len(skill_result["missing_required"])
    if missing_count > 0:
        penalty = missing_count * WEIGHTS["critical_skill_penalty"]
        total *= max(0.0, 1.0 - penalty)

    total = round(min(100, max(0, total)), 2)
    label = get_label(total)

    # Short summary
    matched = skill_result["matched_required"][:3]
    summary_parts = []
    if matched:
        summary_parts.append(f"Matches {', '.join(matched)}")
    if exp_result["candidate_years"]:
        summary_parts.append(f"{exp_result['candidate_years']}y exp")
    if candidate.get("current_title"):
        summary_parts.append(candidate["current_title"])
    short_summary = "; ".join(summary_parts) if summary_parts else "See details"

    return {
        "total_score": total,
        "label": label,
        "short_summary": short_summary,
        "facet_scores": {
            "skill_match": skill_result["score"],
            "experience_match": exp_result["score"],
            "education_match": edu_result["score"],
            "contextual_fit": ctx_result["score"],
        },
        "details": {
            "matched_skills": skill_result["matched_required"] + skill_result["matched_preferred"],
            "missing_skills": skill_result["missing_required"],
            "extra_skills": skill_result["extra_skills"],
            "years_score": exp_result["years_score"],
            "role_score": exp_result["role_score"],
            "domain_score": exp_result["domain_score"],
            "education_level_required": edu_result["required_level"],
            "education_level_candidate": edu_result["candidate_level"],
        },
    }
