"""
Celery tasks – matching and XAI explanation generation.
"""

from __future__ import annotations

import json
import logging
import uuid

import redis as sync_redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from main.celery_app import celery
from main.config import get_settings
from main.services.matching import compute_matches
from main.services.xai import generate_explanation

logger = logging.getLogger(__name__)
settings = get_settings()

_sync_engine = None
_SyncSession = None


def _get_sync_session() -> Session:
    global _sync_engine, _SyncSession
    if _sync_engine is None:
        sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        _sync_engine = create_engine(sync_url, pool_size=5, max_overflow=5)
        _SyncSession = sessionmaker(bind=_sync_engine)
    return _SyncSession()


def _get_redis():
    return sync_redis.from_url(settings.REDIS_URL, decode_responses=True)


@celery.task(bind=True, name="tasks.compute_matches_for_jd", max_retries=2)
def compute_matches_for_jd(self, jd_id: str, company_id: str, top_k: int = 200):
    """
    Full matching pipeline:
    1. Load JD from DB
    2. Run section-wise matching
    3. Store results in matches table
    4. Generate XAI explanations for top candidates
    5. Cache in Redis
    """
    logger.info(f"Computing matches for JD {jd_id}")

    try:
        session = _get_sync_session()
        try:
            from main.models.db_models import JobDescription, Match

            jd = session.query(JobDescription).filter_by(jd_id=uuid.UUID(jd_id)).first()
            if not jd:
                logger.error(f"JD {jd_id} not found")
                return {"error": "JD not found"}

            jd_json = jd.standardised_json or {}
            weights = jd.weights or {}

            if not jd_json:
                logger.warning(f"JD {jd_id} has empty standardised_json, skipping")
                return {"error": "JD not yet processed"}

        finally:
            session.close()

        # Step 2: Compute matches
        match_results = compute_matches(
            jd_id=jd_id,
            company_id=company_id,
            jd_json=jd_json,
            weights=weights,
            top_k=top_k,
        )

        if not match_results:
            logger.info(f"No matches found for JD {jd_id}")
            return {"jd_id": jd_id, "matches": 0}

        # Step 3: Store in DB
        session = _get_sync_session()
        try:
            from main.models.db_models import Match

            for result in match_results:
                existing = session.query(Match).filter_by(
                    jd_id=uuid.UUID(jd_id),
                    candidate_id=uuid.UUID(result["candidate_id"]),
                ).first()

                if existing:
                    existing.total_score = result["total_score"]
                    existing.section_scores = result["section_scores"]
                else:
                    match = Match(
                        jd_id=uuid.UUID(jd_id),
                        candidate_id=uuid.UUID(result["candidate_id"]),
                        total_score=result["total_score"],
                        section_scores=result["section_scores"],
                    )
                    session.add(match)

            session.commit()
        finally:
            session.close()

        # Step 4: Generate XAI for top 50
        top_for_xai = match_results[:50]
        for result in top_for_xai:
            generate_explanation_task.delay(jd_id, result["candidate_id"])

        # Step 5: Cache in Redis
        try:
            r = _get_redis()
            # Build cache-friendly results with candidate info
            cache_results = []
            session = _get_sync_session()
            try:
                from main.models.db_models import Candidate
                for result in match_results:
                    cand = session.query(Candidate).filter_by(
                        candidate_id=uuid.UUID(result["candidate_id"])
                    ).first()
                    cand_json = cand.standardised_json if cand else {}
                    cache_results.append({
                        **result,
                        "id": str(uuid.uuid4()),
                        "candidate_name": cand_json.get("name", "Unknown"),
                        "candidate_summary": cand_json.get("summary", ""),
                        "xai_explanation": None,
                        "recruiter_feedback": None,
                    })
            finally:
                session.close()

            r.setex(
                f"match:{jd_id}",
                settings.MATCH_CACHE_TTL,
                json.dumps(cache_results),
            )
        except Exception as e:
            logger.warning(f"Redis caching failed: {e}")

        logger.info(f"Matching complete for JD {jd_id}: {len(match_results)} results")
        return {"jd_id": jd_id, "matches": len(match_results)}

    except Exception as e:
        logger.error(f"Matching failed for JD {jd_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=15)


@celery.task(bind=True, name="tasks.generate_explanation", max_retries=1)
def generate_explanation_task(self, jd_id: str, candidate_id: str):
    """Generate and store XAI explanation for a specific match."""
    logger.info(f"Generating XAI for JD {jd_id} x Candidate {candidate_id}")

    try:
        session = _get_sync_session()
        try:
            from main.models.db_models import Candidate, JobDescription, Match

            jd = session.query(JobDescription).filter_by(jd_id=uuid.UUID(jd_id)).first()
            cand = session.query(Candidate).filter_by(candidate_id=uuid.UUID(candidate_id)).first()
            match = session.query(Match).filter_by(
                jd_id=uuid.UUID(jd_id),
                candidate_id=uuid.UUID(candidate_id),
            ).first()

            if not all([jd, cand, match]):
                logger.warning("Missing data for XAI generation")
                return

            explanation = generate_explanation(
                jd_json=jd.standardised_json or {},
                candidate_json=cand.standardised_json or {},
                section_scores=match.section_scores or {},
            )

            match.xai_explanation = explanation
            session.commit()

        finally:
            session.close()

        logger.info(f"XAI generated for match {jd_id} x {candidate_id}")
        return {"status": "completed"}

    except Exception as e:
        logger.error(f"XAI generation failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=10)
