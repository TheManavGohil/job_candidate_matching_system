"""
Shared FastAPI dependencies – authentication, DB session, etc.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.db import get_db
from main.models.db_models import Company


async def get_company_from_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Company:
    """
    Extract and validate the company from the X-API-Key header.
    Used as a dependency on all tenant-scoped endpoints.
    """
    result = await db.execute(
        select(Company).where(Company.api_key == x_api_key)
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return company
