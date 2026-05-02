"""
SQLAlchemy ORM models – exact mirror of the PostgreSQL schema in the spec.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from main.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    api_key = Column(Text, unique=True, nullable=False)
    settings = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_descriptions = relationship("JobDescription", back_populates="company", cascade="all, delete-orphan")
    candidates = relationship("Candidate", back_populates="company", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    jd_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(Text, nullable=True)
    standardised_json = Column(JSONB, nullable=False)
    weights = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="job_descriptions")
    matches = relationship("Match", back_populates="job_description", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email_hash = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    standardised_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="candidates")
    matches = relationship("Match", back_populates="candidate", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_candidates_email_hash", "email_hash"),
        Index("idx_candidates_company", "company_id"),
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jd_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.jd_id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    total_score = Column(Float, nullable=False)
    section_scores = Column(JSONB, nullable=False)
    xai_explanation = Column(JSONB, nullable=True)
    recruiter_feedback = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_description = relationship("JobDescription", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")

    __table_args__ = (
        UniqueConstraint("jd_id", "candidate_id", name="idx_match_unique"),
    )
