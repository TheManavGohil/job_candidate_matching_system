"""
Company management endpoints (internal).
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from main.db import get_db
from main.models.db_models import Company
from main.models.schemas import CompanyCreate, CompanyResponse

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    body: CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new company and return its API key."""
    company = Company(
        name=body.name,
        api_key=secrets.token_hex(24),
    )
    db.add(company)
    await db.flush()
    await db.refresh(company)
    return company
