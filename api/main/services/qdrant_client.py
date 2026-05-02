"""
Qdrant vector database operations.
Collections: jd_sections, candidate_sections (vector size 384, cosine).
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from main.config import get_settings
from main.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()

_client: QdrantClient | None = None

JD_COLLECTION = "jd_sections"
CANDIDATE_COLLECTION = "candidate_sections"


def _get_client() -> QdrantClient:
    """Lazy Qdrant client singleton."""
    global _client
    if _client is None:
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=30,
        )
    return _client


def _point_id(text_id: str) -> str:
    """Deterministic UUID5 point ID from a text identifier (required by Qdrant)."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, text_id))


# ═══════════════════════════════════════════════════════════════
#  Collection init
# ═══════════════════════════════════════════════════════════════

def init_collections() -> None:
    """Create collections if they don't already exist."""
    client = _get_client()
    for name in (JD_COLLECTION, CANDIDATE_COLLECTION):
        try:
            client.get_collection(name)
            logger.info(f"Qdrant collection '{name}' already exists")
        except Exception:
            logger.info(f"Creating Qdrant collection '{name}'")
            client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=settings.EMBEDDING_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
            )


# ═══════════════════════════════════════════════════════════════
#  Upsert
# ═══════════════════════════════════════════════════════════════

def upsert_jd_sections(
    jd_id: str,
    company_id: str,
    sections: dict[str, str],
) -> None:
    """Embed and upsert each JD section into Qdrant."""
    client = _get_client()
    emb_service = get_embedding_service()

    points = []
    for section_name, text in sections.items():
        if not text.strip():
            continue
        vector = emb_service.embed_text(text)
        point_id = _point_id(f"{jd_id}_{section_name}")
        points.append(
            qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "company_id": company_id,
                    "jd_id": jd_id,
                    "section": section_name,
                    "text": text[:2000],  # Truncate for payload
                },
            )
        )

    if points:
        client.upsert(collection_name=JD_COLLECTION, points=points)
        logger.info(f"Upserted {len(points)} JD sections for {jd_id}")


def upsert_candidate_sections(
    candidate_id: str,
    company_id: str,
    sections: dict[str, str],
) -> None:
    """Embed and upsert each candidate section into Qdrant."""
    client = _get_client()
    emb_service = get_embedding_service()

    points = []
    for section_name, text in sections.items():
        if not text.strip():
            continue
        vector = emb_service.embed_text(text)
        point_id = _point_id(f"{candidate_id}_{section_name}")
        points.append(
            qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "company_id": company_id,
                    "candidate_id": candidate_id,
                    "section": section_name,
                    "text": text[:2000],
                },
            )
        )

    if points:
        client.upsert(collection_name=CANDIDATE_COLLECTION, points=points)
        logger.info(f"Upserted {len(points)} candidate sections for {candidate_id}")


# ═══════════════════════════════════════════════════════════════
#  Search
# ═══════════════════════════════════════════════════════════════

def search_candidates_by_section(
    section_vector: list[float],
    section_name: str,
    company_id: str,
    top_k: int = 500,
) -> list[dict[str, Any]]:
    """
    Search candidate_sections for candidates matching a JD section.
    Returns list of {candidate_id, score, text}.
    """
    client = _get_client()

    results = client.search(
        collection_name=CANDIDATE_COLLECTION,
        query_vector=section_vector,
        query_filter=qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="company_id",
                    match=qmodels.MatchValue(value=company_id),
                ),
                qmodels.FieldCondition(
                    key="section",
                    match=qmodels.MatchValue(value=section_name),
                ),
            ]
        ),
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "candidate_id": hit.payload.get("candidate_id", ""),
            "score": hit.score,
            "text": hit.payload.get("text", ""),
            "section": hit.payload.get("section", ""),
        }
        for hit in results
    ]


def get_jd_section_vectors(jd_id: str) -> dict[str, list[float]]:
    """Retrieve all section vectors for a JD."""
    client = _get_client()

    results = client.scroll(
        collection_name=JD_COLLECTION,
        scroll_filter=qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="jd_id",
                    match=qmodels.MatchValue(value=jd_id),
                )
            ]
        ),
        with_vectors=True,
        limit=20,
    )

    vectors = {}
    for point in results[0]:
        section = point.payload.get("section", "")
        if section:
            vectors[section] = point.vector
    return vectors


def get_candidate_section_vector(
    candidate_id: str,
    section_name: str,
) -> list[float] | None:
    """Retrieve a specific section vector for a candidate."""
    client = _get_client()
    point_id = _point_id(f"{candidate_id}_{section_name}")
    try:
        results = client.retrieve(
            collection_name=CANDIDATE_COLLECTION,
            ids=[point_id],
            with_vectors=True,
        )
        if results:
            return results[0].vector
    except Exception:
        pass
    return None
