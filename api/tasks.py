"""
Celery tasks for heavy async operations — embedding computation, index rebuilding.
"""

import logging
from celery import Celery

from api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="pickle",
    accept_content=["pickle", "json"],
    result_serializer="pickle",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="tasks.rebuild_faiss_indexes", bind=True)
def rebuild_faiss_indexes(self):
    """Rebuild FAISS indexes from all candidates in the database."""
    import numpy as np
    from api.storage.database import SessionLocal, get_all_candidates, get_candidate_dict
    from api.storage.vector_store import vector_store
    from api.config import get_settings

    settings = get_settings()
    logger.info("Starting FAISS index rebuild...")

    db = SessionLocal()
    try:
        candidates = get_all_candidates(db)
        if not candidates:
            logger.info("No candidates found — building empty indexes")
            vector_store.build_indexes([], np.zeros((0, settings.EMBEDDING_DIM)), np.zeros((0, settings.EMBEDDING_DIM)))
            return {"status": "ok", "count": 0}

        candidate_ids = []
        skill_embeddings = []
        summary_embeddings = []

        for cand in candidates:
            cand_dict = get_candidate_dict(cand)
            cid = cand_dict["candidate_id"]

            skill_emb = cand_dict.get("embedding_skills")
            summary_emb = cand_dict.get("embedding_summary")

            if skill_emb is None:
                skill_emb = np.zeros(settings.EMBEDDING_DIM, dtype=np.float32)
            if summary_emb is None:
                summary_emb = np.zeros(settings.EMBEDDING_DIM, dtype=np.float32)

            candidate_ids.append(cid)
            skill_embeddings.append(skill_emb)
            summary_embeddings.append(summary_emb)

        skill_arr = np.array(skill_embeddings, dtype=np.float32)
        summary_arr = np.array(summary_embeddings, dtype=np.float32)

        vector_store.build_indexes(candidate_ids, skill_arr, summary_arr)
        logger.info(f"FAISS index rebuild complete: {len(candidate_ids)} candidates")

        return {"status": "ok", "count": len(candidate_ids)}
    except Exception as e:
        logger.error(f"FAISS rebuild failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="tasks.process_candidate_batch", bind=True)
def process_candidate_batch(self, candidate_dicts: list):
    """Process a batch of candidates: compute embeddings, store, rebuild index."""
    import numpy as np
    from api.storage.database import SessionLocal, create_candidate
    from api.preprocessing.embeddings import compute_skills_embedding, compute_summary_embedding
    from api.storage.cache import invalidate_match_cache

    logger.info(f"Processing batch of {len(candidate_dicts)} candidates...")

    db = SessionLocal()
    created_ids = []
    try:
        for cand in candidate_dicts:
            # Compute embeddings
            skills = cand.get("skills", [])
            if skills:
                cand["embedding_skills"] = compute_skills_embedding(skills)
            summary = cand.get("work_summary", "")
            if summary:
                cand["embedding_summary"] = compute_summary_embedding(summary)

            result = create_candidate(db, cand)
            created_ids.append(str(result.candidate_id))

        # Rebuild FAISS indexes
        rebuild_faiss_indexes.delay()
        # Invalidate match caches
        invalidate_match_cache()

        logger.info(f"Batch processing complete: {len(created_ids)} candidates created")
        return {"status": "ok", "candidate_ids": created_ids}
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise
    finally:
        db.close()
