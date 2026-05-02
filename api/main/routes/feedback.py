"""
Recruiter feedback endpoint.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.db import get_db
from main.models.db_models import Company, Match
from main.models.schemas import FeedbackRequest, FeedbackResponse
from main.routes.deps import get_company_from_api_key

router = APIRouter(prefix="/api/v1/match", tags=["feedback"])


@router.post(
    "/{jd_id}/{candidate_id}/feedback",
    response_model=FeedbackResponse,
)
async def submit_feedback(
    jd_id: uuid.UUID,
    candidate_id: uuid.UUID,
    body: FeedbackRequest,
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Record recruiter feedback (positive / negative) on a match."""
    result = await db.execute(
        select(Match).where(
            Match.jd_id == jd_id,
            Match.candidate_id == candidate_id,
        )
    )
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    match.recruiter_feedback = body.feedback
    await db.flush()
    return FeedbackResponse(message="Feedback recorded")
