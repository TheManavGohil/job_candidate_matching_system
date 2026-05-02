"""
Centralised application settings loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration knobs live here – one source of truth."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://matcher:matcher_secret@db:5432/matcher_db"
    # Sync URL variant used by Celery tasks (psycopg2)
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Qdrant ────────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None

    # ── LlamaParse ────────────────────────────────────────────
    LLAMA_CLOUD_API_KEY: str | None = None

    # ── Groq LLM ──────────────────────────────────────────────
    GROQ_API_KEY: str = ""

    # ── Auth ──────────────────────────────────────────────────
    JWT_SECRET: str = "change-me"

    # ── Embeddings ────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # ── Matching ──────────────────────────────────────────────
    MAX_CANDIDATES_RETRIEVAL: int = 500
    MATCH_CACHE_TTL: int = 3600  # seconds

    # ── Groq model ────────────────────────────────────────────
    LLM_MODEL: str = "llama-3.3-70b-versatile"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton accessor – settings are parsed once and cached."""
    return Settings()
