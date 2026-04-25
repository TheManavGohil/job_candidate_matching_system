"""
Sentence-transformer embedding wrapper.
Provides functions to compute embeddings for text strings and skill lists.
"""

import logging
from typing import List, Optional
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load the sentence-transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from api.config import get_settings
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    return _model


def compute_embedding(text: str) -> np.ndarray:
    """
    Compute a single embedding vector for a text string.

    Returns:
        (384,) float32 numpy array, L2-normalized.
    """
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.astype(np.float32)


def compute_embeddings_batch(texts: List[str], batch_size: int = 64) -> np.ndarray:
    """
    Compute embeddings for a batch of texts.

    Returns:
        (N, 384) float32 numpy array, L2-normalized.
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
    )
    return embeddings.astype(np.float32)


def compute_skills_embedding(skills: List[str]) -> Optional[np.ndarray]:
    """
    Compute a single embedding representing a set of skills.
    Strategy: embed each skill individually, then average.

    Returns:
        (384,) float32 numpy array, or None if no skills.
    """
    if not skills:
        return None

    model = _get_model()
    embeddings = model.encode(skills, normalize_embeddings=True)
    avg = np.mean(embeddings, axis=0).astype(np.float32)

    # Re-normalize the average
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm

    return avg


def compute_summary_embedding(text: Optional[str]) -> Optional[np.ndarray]:
    """
    Compute embedding for a summary/description text.

    Returns:
        (384,) float32 numpy array, or None if text is empty.
    """
    if not text or not text.strip():
        return None
    return compute_embedding(text.strip())


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0

    a = a.flatten().astype(np.float32)
    b = b.flatten().astype(np.float32)

    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot / (norm_a * norm_b))
