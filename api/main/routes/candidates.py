"""
Candidate endpoints – upload (single/bulk), view.
"""

from __future__ import annotations

import base64
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.db import get_db
from main.models.db_models import Candidate, Company
from main.models.schemas import CandidateResponse, CandidateUploadResponse
from main.routes.deps import get_company_from_api_key

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.post("/upload", response_model=CandidateUploadResponse, status_code=201)
async def upload_candidates(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload candidate data.
    - Single file: PDF or DOCX resume  →  1 candidate
    - CSV file                         →  N candidates (one per row)
    - Raw text                         →  1 candidate
    """
    if file is None and text is None:
        raise HTTPException(status_code=400, detail="Provide either a file or text")

    filename = file.filename if file else "text_input.txt"
    file_bytes = await file.read() if file else text.encode("utf-8")

    is_batch = filename.lower().endswith(".csv") or filename.lower().endswith(".xlsx")

    if is_batch:
        # For CSV, create a batch task
        candidate_id = uuid.uuid4()  # placeholder; actual IDs created in task
        candidate = Candidate(
            candidate_id=candidate_id,
            company_id=company.id,
            standardised_json={},
            raw_text="[Batch processing]",
        )
        db.add(candidate)
        await db.flush()

        from main.tasks.processing import process_candidate_batch
        task = process_candidate_batch.delay(
            base64.b64encode(file_bytes).decode(),
            filename,
            str(company.id),
        )
        return CandidateUploadResponse(candidate_ids=[candidate_id], task_ids=[task.id])
    else:
        # Single candidate
        candidate_id = uuid.uuid4()
        candidate = Candidate(
            candidate_id=candidate_id,
            company_id=company.id,
            standardised_json={},
            raw_text="",
        )
        db.add(candidate)
        await db.flush()

        from main.tasks.processing import process_candidate
        task = process_candidate.delay(
            str(candidate_id),
            base64.b64encode(file_bytes).decode(),
            filename,
            str(company.id),
        )
        return CandidateUploadResponse(candidate_ids=[candidate_id], task_ids=[task.id])


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: uuid.UUID,
    company: Company = Depends(get_company_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Return a standardised candidate profile."""
    result = await db.execute(
        select(Candidate).where(
            Candidate.candidate_id == candidate_id,
            Candidate.company_id == company.id,
        )
    )
    cand = result.scalar_one_or_none()
    if cand is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand
