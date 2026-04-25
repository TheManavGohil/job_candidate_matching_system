"""
PostgreSQL database layer — SQLAlchemy models and CRUD operations.
"""

import logging
import json
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    create_engine, Column, Text, Float, ARRAY, DateTime, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.sql import func

from api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ───────────────────────────────────────────────────────────────

class JobORM(Base):
    __tablename__ = "jobs"

    jd_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    title = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=False)
    required_skills = Column(ARRAY(Text), default=[])
    preferred_skills = Column(ARRAY(Text), default=[])
    min_years = Column(Float, nullable=True)
    role_type = Column(Text, nullable=True)
    core_requirements_text = Column(Text, nullable=True)
    embedding_skills = Column(Text, nullable=True)   # JSON-serialized float list
    embedding_summary = Column(Text, nullable=True)  # JSON-serialized float list
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateORM(Base):
    __tablename__ = "candidates"

    candidate_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name = Column(Text, nullable=True)
    email = Column(Text, nullable=True, unique=True)
    raw_data = Column(JSONB, nullable=True)
    skills = Column(ARRAY(Text), default=[])
    years_of_experience = Column(Float, nullable=True)
    education = Column(Text, nullable=True)
    current_title = Column(Text, nullable=True)
    work_summary = Column(Text, nullable=True)
    embedding_skills = Column(Text, nullable=True)
    embedding_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Database helpers ─────────────────────────────────────────────────────────

def get_db() -> Session:
    """Dependency for FastAPI — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def _serialize_embedding(embedding) -> Optional[str]:
    """Convert numpy array to JSON string for storage."""
    if embedding is None:
        return None
    return json.dumps(embedding.tolist() if hasattr(embedding, "tolist") else list(embedding))


def _deserialize_embedding(data: Optional[str]):
    """Convert JSON string back to list of floats."""
    if data is None:
        return None
    import numpy as np
    return np.array(json.loads(data), dtype=np.float32)


# ── Job CRUD ─────────────────────────────────────────────────────────────────

def create_job(db: Session, job_data: Dict[str, Any]) -> JobORM:
    jd_id = str(uuid4())
    job = JobORM(
        jd_id=jd_id,
        title=job_data.get("title"),
        raw_text=job_data["raw_text"],
        required_skills=job_data.get("required_skills", []),
        preferred_skills=job_data.get("preferred_skills", []),
        min_years=job_data.get("min_years"),
        role_type=job_data.get("role_type"),
        core_requirements_text=job_data.get("core_requirements_text"),
        embedding_skills=_serialize_embedding(job_data.get("embedding_skills")),
        embedding_summary=_serialize_embedding(job_data.get("embedding_summary")),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"Created job {jd_id}: {job.title}")
    return job


def get_job(db: Session, jd_id: str) -> Optional[JobORM]:
    return db.query(JobORM).filter(JobORM.jd_id == jd_id).first()


def list_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[JobORM]:
    return (
        db.query(JobORM)
        .order_by(JobORM.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_job_dict(job: JobORM) -> Dict[str, Any]:
    """Convert ORM object to plain dict for matching engine."""
    return {
        "jd_id": str(job.jd_id),
        "title": job.title,
        "raw_text": job.raw_text,
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "min_years": job.min_years,
        "role_type": job.role_type,
        "core_requirements_text": job.core_requirements_text,
        "embedding_skills": _deserialize_embedding(job.embedding_skills),
        "embedding_summary": _deserialize_embedding(job.embedding_summary),
    }


# ── Candidate CRUD ───────────────────────────────────────────────────────────

def create_candidate(db: Session, cand_data: Dict[str, Any]) -> CandidateORM:
    candidate_id = str(uuid4())

    # Handle potential duplicate emails gracefully
    email = cand_data.get("email")
    if email:
        existing = db.query(CandidateORM).filter(CandidateORM.email == email).first()
        if existing:
            # Update existing candidate
            for key, val in cand_data.items():
                if key in ("embedding_skills", "embedding_summary"):
                    setattr(existing, key, _serialize_embedding(val))
                elif hasattr(existing, key):
                    setattr(existing, key, val)
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated existing candidate {existing.candidate_id}: {existing.name}")
            return existing

    candidate = CandidateORM(
        candidate_id=candidate_id,
        name=cand_data.get("name"),
        email=email,
        raw_data=cand_data.get("raw_data"),
        skills=cand_data.get("skills", []),
        years_of_experience=cand_data.get("years_of_experience"),
        education=cand_data.get("education"),
        current_title=cand_data.get("current_title"),
        work_summary=cand_data.get("work_summary"),
        embedding_skills=_serialize_embedding(cand_data.get("embedding_skills")),
        embedding_summary=_serialize_embedding(cand_data.get("embedding_summary")),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    logger.info(f"Created candidate {candidate_id}: {candidate.name}")
    return candidate


def get_candidate(db: Session, candidate_id: str) -> Optional[CandidateORM]:
    return db.query(CandidateORM).filter(CandidateORM.candidate_id == candidate_id).first()


def list_candidates(db: Session, skip: int = 0, limit: int = 100) -> List[CandidateORM]:
    return (
        db.query(CandidateORM)
        .order_by(CandidateORM.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_candidates(db: Session) -> List[CandidateORM]:
    """Get all candidates — used for FAISS index building."""
    return db.query(CandidateORM).all()


def get_candidate_dict(cand: CandidateORM) -> Dict[str, Any]:
    """Convert ORM object to plain dict for matching engine."""
    return {
        "candidate_id": str(cand.candidate_id),
        "name": cand.name,
        "email": cand.email,
        "raw_data": cand.raw_data,
        "skills": cand.skills or [],
        "years_of_experience": cand.years_of_experience,
        "education": cand.education,
        "current_title": cand.current_title,
        "work_summary": cand.work_summary,
        "embedding_skills": _deserialize_embedding(cand.embedding_skills),
        "embedding_summary": _deserialize_embedding(cand.embedding_summary),
    }


def get_candidates_by_ids(db: Session, candidate_ids: List[str]) -> List[CandidateORM]:
    """Fetch multiple candidates by their IDs."""
    return (
        db.query(CandidateORM)
        .filter(CandidateORM.candidate_id.in_(candidate_ids))
        .all()
    )
