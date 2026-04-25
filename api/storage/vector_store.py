"""
FAISS vector store wrapper — manages skill and summary indexes.
"""

import logging
import os
import pickle
from typing import List, Tuple, Optional, Dict

import faiss
import numpy as np

from api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Dimension of our embeddings (all-MiniLM-L6-v2 produces 384-d vectors)
DIM = settings.EMBEDDING_DIM


class VectorStore:
    """
    Manages two FAISS indexes:
      - skill_index:   candidate skill embeddings
      - summary_index: candidate summary embeddings

    Candidate IDs are tracked in parallel lists so we can map
    FAISS result positions back to UUIDs.
    """

    def __init__(self):
        self.skill_index: Optional[faiss.IndexFlatIP] = None
        self.summary_index: Optional[faiss.IndexFlatIP] = None
        self.candidate_ids: List[str] = []
        self._index_dir = settings.FAISS_INDEX_DIR
        os.makedirs(self._index_dir, exist_ok=True)

    # ── Build / Rebuild ──────────────────────────────────────────────────

    def build_indexes(
        self,
        candidate_ids: List[str],
        skill_embeddings: np.ndarray,
        summary_embeddings: np.ndarray,
    ):
        """
        Build both FAISS indexes from scratch.

        Args:
            candidate_ids: list of UUID strings, same order as embeddings.
            skill_embeddings: (N, 384) float32 array, L2-normalized.
            summary_embeddings: (N, 384) float32 array, L2-normalized.
        """
        n = len(candidate_ids)
        if n == 0:
            self.skill_index = faiss.IndexFlatIP(DIM)
            self.summary_index = faiss.IndexFlatIP(DIM)
            self.candidate_ids = []
            logger.info("Built empty FAISS indexes")
            return

        # Ensure float32 and normalized
        skill_embeddings = self._normalize(skill_embeddings.astype(np.float32))
        summary_embeddings = self._normalize(summary_embeddings.astype(np.float32))

        self.skill_index = faiss.IndexFlatIP(DIM)
        self.summary_index = faiss.IndexFlatIP(DIM)

        self.skill_index.add(skill_embeddings)
        self.summary_index.add(summary_embeddings)
        self.candidate_ids = list(candidate_ids)

        logger.info(f"Built FAISS indexes with {n} candidates")
        self._save()

    def add_candidates(
        self,
        candidate_ids: List[str],
        skill_embeddings: np.ndarray,
        summary_embeddings: np.ndarray,
    ):
        """Add new candidates to existing indexes (incremental)."""
        if self.skill_index is None:
            self.build_indexes(candidate_ids, skill_embeddings, summary_embeddings)
            return

        skill_embeddings = self._normalize(skill_embeddings.astype(np.float32))
        summary_embeddings = self._normalize(summary_embeddings.astype(np.float32))

        self.skill_index.add(skill_embeddings)
        self.summary_index.add(summary_embeddings)
        self.candidate_ids.extend(candidate_ids)

        logger.info(f"Added {len(candidate_ids)} candidates to FAISS indexes")
        self._save()

    # ── Search ───────────────────────────────────────────────────────────

    def search_summary(
        self, query_embedding: np.ndarray, top_k: int = 2000
    ) -> List[Tuple[str, float]]:
        """
        Search summary_index for candidates most similar to the query.

        Returns list of (candidate_id, cosine_similarity) tuples.
        """
        if self.summary_index is None or self.summary_index.ntotal == 0:
            return []

        query = self._normalize(query_embedding.reshape(1, -1).astype(np.float32))
        k = min(top_k, self.summary_index.ntotal)
        scores, indices = self.summary_index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.candidate_ids):
                results.append((self.candidate_ids[idx], float(score)))
        return results

    def search_skills(
        self, query_embedding: np.ndarray, top_k: int = 2000
    ) -> List[Tuple[str, float]]:
        """Search skill_index similarly."""
        if self.skill_index is None or self.skill_index.ntotal == 0:
            return []

        query = self._normalize(query_embedding.reshape(1, -1).astype(np.float32))
        k = min(top_k, self.skill_index.ntotal)
        scores, indices = self.skill_index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.candidate_ids):
                results.append((self.candidate_ids[idx], float(score)))
        return results

    # ── Persistence ──────────────────────────────────────────────────────

    def _save(self):
        """Save indexes and ID mapping to disk."""
        try:
            if self.skill_index:
                faiss.write_index(
                    self.skill_index,
                    os.path.join(self._index_dir, "skill_index.faiss"),
                )
            if self.summary_index:
                faiss.write_index(
                    self.summary_index,
                    os.path.join(self._index_dir, "summary_index.faiss"),
                )
            with open(os.path.join(self._index_dir, "candidate_ids.pkl"), "wb") as f:
                pickle.dump(self.candidate_ids, f)
            logger.info("Saved FAISS indexes to disk")
        except Exception as e:
            logger.error(f"Failed to save FAISS indexes: {e}")

    def load(self):
        """Load indexes from disk if they exist."""
        skill_path = os.path.join(self._index_dir, "skill_index.faiss")
        summary_path = os.path.join(self._index_dir, "summary_index.faiss")
        ids_path = os.path.join(self._index_dir, "candidate_ids.pkl")

        if os.path.exists(skill_path) and os.path.exists(summary_path) and os.path.exists(ids_path):
            self.skill_index = faiss.read_index(skill_path)
            self.summary_index = faiss.read_index(summary_path)
            with open(ids_path, "rb") as f:
                self.candidate_ids = pickle.load(f)
            logger.info(
                f"Loaded FAISS indexes from disk ({self.skill_index.ntotal} candidates)"
            )
        else:
            logger.info("No FAISS indexes found on disk — starting fresh")
            self.skill_index = faiss.IndexFlatIP(DIM)
            self.summary_index = faiss.IndexFlatIP(DIM)
            self.candidate_ids = []

    # ── Utils ────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(embeddings: np.ndarray) -> np.ndarray:
        """L2-normalize embeddings for cosine similarity via inner product."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms


# Module-level singleton
vector_store = VectorStore()
