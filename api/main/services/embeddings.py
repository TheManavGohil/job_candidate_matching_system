"""
Embedding service – local SentenceTransformer wrapper with caching.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import numpy as np

from main.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model = None


class EmbeddingService:
    """Wraps sentence-transformers for 384-dim MiniLM embeddings."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dim = settings.EMBEDDING_DIM

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string. Returns 384-dim vector."""
        if not text.strip():
            return [0.0] * self.dim
        vec = self.model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of 384-dim vectors."""
        if not texts:
            return []
        # Replace empty strings with a placeholder
        cleaned = [t if t.strip() else "empty" for t in texts]
        vecs = self.model.encode(cleaned, normalize_embeddings=True, batch_size=64)
        return vecs.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Singleton accessor – model loaded once."""
    return EmbeddingService()
