"""
Application configuration — loaded from environment variables.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost:5432/matchdb",
    )

    # Redis (SSL-ready for Azure)
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "rediss://localhost:6379/0",
    )

    # Celery (reuse Redis URL by default)
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL",
        REDIS_URL,
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        REDIS_URL,
    )

    # Embedding model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # FAISS
    FAISS_INDEX_DIR: str = os.getenv("FAISS_INDEX_DIR", "/app/faiss_indexes")

    # Cache TTL (seconds)
    MATCH_CACHE_TTL: int = 3600
    CANDIDATE_CACHE_TTL: int = 1800
    JD_CACHE_TTL: int = 1800

    # Matching defaults
    DEFAULT_TOP_K: int = 50
    DEFAULT_THRESHOLD: float = 50.0
    FAISS_PREFETCH_K: int = 2000

    # spaCy model
    SPACY_MODEL: str = "en_core_web_sm"

    # API
    API_PREFIX: str = "/api"

    # CORS (env-based for cloud flexibility)
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()