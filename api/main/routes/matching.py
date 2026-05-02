"""
Matching endpoints – trigger, list results, get individual explanation.
"""

from __future__ import annotations

import json
import uuid

import redis as sync_redis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.config import get_settings
from main.db import get_db
from main.models.db_models import Candidate, Company, JobDescription, Match
from main.models.schemas import (
    MatchListResponse,
    MatchResult,
    MatchTriggerResponse,
)
from main.routes.deps import get_company_from_api_key

router = APIRouter(prefix="/api/v1/match", tags=["matching"])
settings = get_settings()


def _get_redis():
    return sync_redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.post("/{jd_id}", response_model=MatchTriggerResponse, status_code=202)
async def trigger_matching(
    jd_id: uuid.UUID,
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Trigger asynchronous matching for a JD. Returns a Celery task_id."""
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.jd_id == jd_id,
            JobDescription.company_id == company.id,
        )
    )
    jd = result.scalar_one_or_none()
    if jd is None:
        raise HTTPException(status_code=404, detail="JD not found")

    from main.tasks.matching import compute_matches_for_jd
    task = compute_matches_for_jd.delay(str(jd_id), str(company.id))

    return MatchTriggerResponse(task_id=task.id, jd_id=jd_id)


@router.get("/{jd_id}", response_model=MatchListResponse)
async def get_match_results(
    jd_id: uuid.UUID,
    top_k: int = Query(50, ge=1, le=500),
    threshold: float = Query(0.0, ge=0.0, le=100.0),
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Return ranked match results for a JD, from cache or DB."""
    # Try Redis cache first
    r = _get_redis()
    cache_key = f"match:{jd_id}"
    cached = r.get(cache_key)

    if cached:
        all_results = json.loads(cached)
        # Merge live XAI explanations from DB (cache is populated before XAI tasks finish)
        try:
            for item in all_results:
                cid = item.get("candidate_id")
                jd_uuid = jd_id
                if cid:
                    match_result = await db.execute(
                        select(Match).where(
                            Match.jd_id == jd_uuid,
                            Match.candidate_id == uuid.UUID(cid),
                        )
                    )
                    m = match_result.scalar_one_or_none()
                    if m and m.xai_explanation:
                        item["xai_explanation"] = m.xai_explanation
                        item["recruiter_feedback"] = m.recruiter_feedback
        except Exception:
            pass  # Best-effort; don't break the response
    else:
        # Fall back to DB
        result = await db.execute(
            select(Match)
            .where(Match.jd_id == jd_id)
            .order_by(Match.total_score.desc())
        )
        matches = result.scalars().all()
        all_results = []
        for m in matches:
            # Fetch candidate name from standardised_json
            cand_result = await db.execute(
                select(Candidate).where(Candidate.candidate_id == m.candidate_id)
            )
            cand = cand_result.scalar_one_or_none()
            cand_json = cand.standardised_json if cand else {}

            all_results.append({
                "id": str(m.id),
                "candidate_id": str(m.candidate_id),
                "total_score": m.total_score,
                "section_scores": m.section_scores,
                "xai_explanation": m.xai_explanation,
                "candidate_name": cand_json.get("name", "Unknown"),
                "candidate_summary": cand_json.get("summary", ""),
                "recruiter_feedback": m.recruiter_feedback,
            })

    # Filter by threshold and limit
    filtered = [
        r for r in all_results
        if r["total_score"] >= threshold
    ][:top_k]

    return MatchListResponse(
        jd_id=jd_id,
        total=len(filtered),
        results=filtered,
    )


@router.get("/{jd_id}/{candidate_id}", response_model=MatchResult)
async def get_match_detail(
    jd_id: uuid.UUID,
    candidate_id: uuid.UUID,
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Return full XAI explanation and section scores for one candidate."""
    result = await db.execute(
        select(Match).where(
            Match.jd_id == jd_id,
            Match.candidate_id == candidate_id,
        )
    )
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    cand_result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id)
    )
    cand = cand_result.scalar_one_or_none()
    cand_json = cand.standardised_json if cand else {}

    return MatchResult(
        id=match.id,
        candidate_id=match.candidate_id,
        total_score=match.total_score,
        section_scores=match.section_scores,
        xai_explanation=match.xai_explanation,
        candidate_name=cand_json.get("name", "Unknown"),
        candidate_summary=cand_json.get("summary", ""),
        recruiter_feedback=match.recruiter_feedback,
    )
