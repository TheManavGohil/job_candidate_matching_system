"""
FastAPI application entry-point with lifespan management.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from main.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle."""
    # ── Startup ───────────────────────────────────────────────
    await init_db()

    # Pre-load embedding model (warm the cache)
    from main.services.embeddings import get_embedding_service
    get_embedding_service()

    # Ensure Qdrant collections exist (run in threadpool – sync client)
    from main.services.qdrant_client import init_collections
    try:
        await asyncio.to_thread(init_collections)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Qdrant init skipped: {e}")

    yield
    # ── Shutdown ──────────────────────────────────────────────
    # (nothing to clean up; engine pool handles itself)


app = FastAPI(
    title="Job-Candidate Matching Engine",
    description="Explainable AI-powered candidate ranking with section-wise semantic matching",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
from main.routes.companies import router as companies_router   # noqa: E402
from main.routes.jobs import router as jobs_router             # noqa: E402
from main.routes.candidates import router as candidates_router # noqa: E402
from main.routes.matching import router as matching_router     # noqa: E402
from main.routes.feedback import router as feedback_router     # noqa: E402
from main.routes.sdk import router as sdk_router               # noqa: E402

app.include_router(companies_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(matching_router)
app.include_router(feedback_router)
app.include_router(sdk_router)


@app.get("/api/v1/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "matching-engine"}
