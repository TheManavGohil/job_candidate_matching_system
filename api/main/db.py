"""
Async SQLAlchemy engine, session factory, and startup helpers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from main.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency – yields an async session then closes it."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Run on application startup:
    1. Create pgcrypto + pgvector extensions using AUTOCOMMIT (no transaction).
    2. Create all ORM tables if they don't exist.
    """
    # CREATE EXTENSION cannot run inside a transaction block in PostgreSQL.
    # We use an engine with AUTOCOMMIT isolation level for this step only.
    autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")
    async with autocommit_engine.connect() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS pgcrypto'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

    # Now create all ORM tables inside a normal transaction.
    async with engine.begin() as conn:
        import main.models.db_models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

    await ensure_default_company()


# ── Default company (no-auth demo mode) ──────────────────────────────────────
DEFAULT_API_KEY = "matchiq-default-key-2024"


async def ensure_default_company() -> None:
    """Ensure a default company exists so the frontend works without login."""
    from sqlalchemy import select
    from main.models.db_models import Company
    import uuid

    async with async_session_factory() as session:
        result = await session.execute(
            select(Company).where(Company.api_key == DEFAULT_API_KEY)
        )
        if result.scalar_one_or_none() is None:
            company = Company(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="MatchIQ Default",
                api_key=DEFAULT_API_KEY,
            )
            session.add(company)
            await session.commit()
