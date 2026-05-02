"""
Celery tasks – document processing (JD + candidate).
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from main.celery_app import celery
from main.config import get_settings
from main.services.parsing import extract_entities, extract_text, split_sections
from main.services.standardisation import standardise_candidate, standardise_jd
from main.services.qdrant_client import upsert_candidate_sections, upsert_jd_sections
from main.utils.helpers import clean_text, sha256_hash

logger = logging.getLogger(__name__)
settings = get_settings()

# Sync DB engine for Celery (cannot use async)
_sync_engine = None
_SyncSession = None


def _get_sync_session() -> Session:
    global _sync_engine, _SyncSession
    if _sync_engine is None:
        sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        _sync_engine = create_engine(sync_url, pool_size=5, max_overflow=5)
        _SyncSession = sessionmaker(bind=_sync_engine)
    return _SyncSession()


@celery.task(bind=True, name="tasks.process_job_description", max_retries=2)
def process_job_description(self, jd_id: str, file_bytes_b64: str, filename: str, company_id: str):
    """
    Process a Job Description:
    1. Extract text (PDF/DOCX/TXT)
    2. Split into sections
    3. LLM standardisation
    4. Embed & store in Qdrant
    5. Update DB row
    """
    logger.info(f"Processing JD {jd_id} from {filename}")

    try:
        file_bytes = base64.b64decode(file_bytes_b64)

        # Step 1: Extract text
        raw_text = extract_text(file_bytes, filename)
        raw_text = clean_text(raw_text)

        # Step 2: Split sections
        sections = split_sections(raw_text)

        # Step 3: LLM standardisation
        standardised = standardise_jd(raw_text, sections)

        # Step 4: Build sections for embedding
        embed_sections = {}
        if standardised.get("required_skills"):
            embed_sections["required_skills"] = ", ".join(standardised["required_skills"])
        if standardised.get("preferred_skills"):
            embed_sections["preferred_skills"] = ", ".join(standardised["preferred_skills"])
        if standardised.get("responsibilities"):
            embed_sections["responsibilities"] = ". ".join(standardised["responsibilities"])
        quals = standardised.get("qualifications", {})
        if isinstance(quals, dict):
            quals_text = f"{quals.get('degree', '')} in {quals.get('field', '')}, {quals.get('min_years', 0)}+ years"
            embed_sections["qualifications"] = quals_text
        if standardised.get("context"):
            embed_sections["context"] = standardised["context"]

        # Upsert to Qdrant
        upsert_jd_sections(jd_id, company_id, embed_sections)

        # Step 5: Update DB
        session = _get_sync_session()
        try:
            from main.models.db_models import JobDescription
            jd = session.query(JobDescription).filter_by(jd_id=uuid.UUID(jd_id)).first()
            if jd:
                jd.raw_text = raw_text
                jd.standardised_json = standardised
                session.commit()
            else:
                logger.error(f"JD {jd_id} not found in DB")
        finally:
            session.close()

        logger.info(f"JD {jd_id} processed successfully")
        return {"jd_id": jd_id, "status": "completed"}

    except Exception as e:
        logger.error(f"JD processing failed for {jd_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=10)


@celery.task(bind=True, name="tasks.process_candidate", max_retries=2)
def process_candidate(self, candidate_id: str, file_bytes_b64: str, filename: str, company_id: str):
    """
    Process a single candidate:
    1. Extract text
    2. NER (name, email, phone)
    3. Split sections
    4. LLM standardisation
    5. Embed & store in Qdrant
    6. Update DB
    """
    logger.info(f"Processing candidate {candidate_id} from {filename}")

    try:
        file_bytes = base64.b64decode(file_bytes_b64)

        # Step 1: Extract text
        raw_text = extract_text(file_bytes, filename)
        raw_text = clean_text(raw_text)

        # Step 2: NER
        entities = extract_entities(raw_text)

        # Step 3: Split sections
        sections = split_sections(raw_text)

        # Step 4: LLM standardisation
        standardised = standardise_candidate(raw_text, sections)

        # Merge NER results
        if entities.get("name") and not standardised.get("name"):
            standardised["name"] = entities["name"]

        # Step 5: Build sections for embedding
        embed_sections = {}
        if standardised.get("skills"):
            embed_sections["skills"] = ", ".join(standardised["skills"])
        if standardised.get("experience"):
            exp_texts = []
            for exp in standardised["experience"]:
                if isinstance(exp, dict):
                    exp_texts.append(f"{exp.get('role', '')} at {exp.get('company', '')}: {exp.get('description', '')}")
            embed_sections["experience"] = ". ".join(exp_texts)
        if standardised.get("education"):
            edu_texts = []
            for edu in standardised["education"]:
                if isinstance(edu, dict):
                    edu_texts.append(f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}")
            embed_sections["education"] = ". ".join(edu_texts)
        if standardised.get("projects"):
            proj_texts = []
            for proj in standardised["projects"]:
                if isinstance(proj, dict):
                    proj_texts.append(f"{proj.get('name', '')}: {proj.get('description', '')}")
            embed_sections["projects"] = ". ".join(proj_texts)

        # Upsert to Qdrant – always embed at least the raw text so the candidate is searchable
        if not embed_sections:
            logger.warning(f"No structured sections for candidate {candidate_id}, embedding raw text as fallback")
            embed_sections["skills"] = raw_text[:2000]
            embed_sections["experience"] = raw_text[:2000]

        # Upsert to Qdrant
        upsert_candidate_sections(candidate_id, company_id, embed_sections)

        # Step 6: Update DB
        email_hash = sha256_hash(entities["email"]) if entities.get("email") else None
        session = _get_sync_session()
        try:
            from main.models.db_models import Candidate
            cand = session.query(Candidate).filter_by(candidate_id=uuid.UUID(candidate_id)).first()
            if cand:
                cand.raw_text = raw_text
                cand.standardised_json = standardised
                cand.email_hash = email_hash
                session.commit()
        finally:
            session.close()

        logger.info(f"Candidate {candidate_id} processed successfully")
        return {"candidate_id": candidate_id, "status": "completed"}

    except Exception as e:
        logger.error(f"Candidate processing failed for {candidate_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=10)


@celery.task(bind=True, name="tasks.process_candidate_batch", max_retries=1)
def process_candidate_batch(self, file_bytes_b64: str, filename: str, company_id: str):
    """
    Process a CSV of candidates – create one candidate per row,
    dispatch individual processing tasks.
    """
    logger.info(f"Processing candidate batch from {filename}")

    try:
        file_bytes = base64.b64decode(file_bytes_b64)
        
        import pandas as pd
        if filename.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            # Fallback to CSV
            text = file_bytes.decode("utf-8", errors="replace")
            df = pd.read_csv(io.StringIO(text))

        candidate_ids = []
        session = _get_sync_session()

        try:
            from main.models.db_models import Candidate

            for _, row in df.iterrows():
                # Build raw text from all columns
                raw_text = "\n".join(f"{k}: {v}" for k, v in row.items() if pd.notna(v))
                candidate_id = uuid.uuid4()

                cand = Candidate(
                    candidate_id=candidate_id,
                    company_id=uuid.UUID(company_id),
                    raw_text=raw_text,
                    standardised_json={},
                )
                session.add(cand)
                candidate_ids.append(str(candidate_id))

            session.commit()
        finally:
            session.close()

        # Dispatch individual tasks
        for cid in candidate_ids:
            # Re-encode each candidate's raw text
            session = _get_sync_session()
            try:
                from main.models.db_models import Candidate
                cand = session.query(Candidate).filter_by(candidate_id=uuid.UUID(cid)).first()
                if cand and cand.raw_text:
                    raw_b64 = base64.b64encode(cand.raw_text.encode()).decode()
                    process_candidate.delay(cid, raw_b64, "csv_row.txt", company_id)
            finally:
                session.close()

        logger.info(f"Dispatched {len(candidate_ids)} candidate processing tasks")
        return {"candidate_ids": candidate_ids, "status": "dispatched"}

    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=10)
