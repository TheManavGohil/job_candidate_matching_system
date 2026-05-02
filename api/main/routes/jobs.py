"""
Job Description endpoints – upload, view, update weights.
"""

from __future__ import annotations

import base64
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.db import get_db
from main.models.db_models import Company, JobDescription
from main.models.schemas import (
    DefaultWeights,
    JDResponse,
    JDUploadResponse,
    WeightsUpdate,
)
from main.routes.deps import get_company_from_api_key

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/upload", response_model=JDUploadResponse, status_code=201)
async def upload_job_description(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Upload a JD file (PDF/DOCX/TXT) or raw text. Triggers async processing."""
    if file is None and text is None:
        raise HTTPException(status_code=400, detail="Provide either a file or text")

    jd_id = uuid.uuid4()
    filename = file.filename if file else "text_input.txt"

    if file:
        file_bytes = await file.read()
    else:
        file_bytes = text.encode("utf-8") if text else b""

    # Create placeholder row so the ID is immediately usable
    default_weights = DefaultWeights().model_dump()
    jd = JobDescription(
        jd_id=jd_id,
        company_id=company.id,
        raw_text=text or "",
        standardised_json={},
        weights=default_weights,
    )
    db.add(jd)
    await db.flush()

    # Dispatch Celery task
    from main.tasks.processing import process_job_description
    task = process_job_description.delay(
        str(jd_id),
        base64.b64encode(file_bytes).decode(),
        filename,
        str(company.id),
    )

    return JDUploadResponse(jd_id=jd_id, task_id=task.id)


@router.put("/{jd_id}/weights", response_model=JDResponse)
async def update_weights(
    jd_id: uuid.UUID,
    body: WeightsUpdate,
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Update section weights for a JD. Weights are normalised to sum to 100."""
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.jd_id == jd_id,
            JobDescription.company_id == company.id,
        )
    )
    jd = result.scalar_one_or_none()
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")

    # Normalise weights to sum to 100
    raw = body.weights
    total = sum(raw.values()) or 1
    normalised = {k: round(v / total * 100, 2) for k, v in raw.items()}
    jd.weights = normalised
    await db.flush()
    await db.refresh(jd)
    return jd


@router.get("", response_model=list[JDResponse])
async def list_job_descriptions(
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Return all JDs for the current company, newest first."""
    result = await db.execute(
        select(JobDescription)
        .where(JobDescription.company_id == company.id)
        .order_by(JobDescription.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{jd_id}", response_model=JDResponse)
async def get_job_description(
    jd_id: uuid.UUID,
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Return the full JD with weights."""
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.jd_id == jd_id,
            JobDescription.company_id == company.id,
        )
    )
    jd = result.scalar_one_or_none()
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd
