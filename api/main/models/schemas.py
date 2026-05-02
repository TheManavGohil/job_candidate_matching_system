"""
Pydantic v2 request / response schemas for every entity.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
#  Company
# ═══════════════════════════════════════════════════════════════
class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Job Description – Standardised
# ═══════════════════════════════════════════════════════════════
class JDStandardised(BaseModel):
    title: str = ""
    company_context: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: dict[str, Any] = Field(default_factory=dict)  # {degree, field, min_years}
    context: str = ""
    evidence: dict[str, str] = Field(default_factory=dict)


class DefaultWeights(BaseModel):
    required_skills: float = 30.0
    preferred_skills: float = 10.0
    responsibilities: float = 25.0
    qualifications: float = 20.0
    context: float = 15.0


class WeightsUpdate(BaseModel):
    weights: dict[str, float]


class JDUploadResponse(BaseModel):
    jd_id: uuid.UUID
    task_id: str | None = None
    standardised_json: dict | None = None

class JDResponse(BaseModel):
    jd_id: uuid.UUID
    company_id: uuid.UUID
    raw_text: str | None = None
    standardised_json: dict
    weights: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Candidate – Standardised
# ═══════════════════════════════════════════════════════════════
class ExperienceEntry(BaseModel):
    company: str = ""
    role: str = ""
    duration: str = ""
    description: str = ""

class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    year: str = ""

class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    tech: list[str] = Field(default_factory=list)

class CandidateStandardised(BaseModel):
    name: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    total_years: float = 0.0
    summary: str = ""

class CandidateUploadResponse(BaseModel):
    candidate_ids: list[uuid.UUID]
    task_ids: list[str] = Field(default_factory=list)

class CandidateResponse(BaseModel):
    candidate_id: uuid.UUID
    company_id: uuid.UUID
    standardised_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  XAI Explanation
# ═══════════════════════════════════════════════════════════════
class StrengthWeakness(BaseModel):
    point: str
    evidence: str

class XAIExplanation(BaseModel):
    overall_grade: str  # "Strong Match" | "Good Fit" | "Potential" | "Not Recommended"
    strengths: list[StrengthWeakness] = Field(default_factory=list)
    weaknesses: list[StrengthWeakness] = Field(default_factory=list)
    recommendation: str = ""


# ═══════════════════════════════════════════════════════════════
#  Matching
# ═══════════════════════════════════════════════════════════════
class MatchResult(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    total_score: float
    section_scores: dict[str, float]
    xai_explanation: XAIExplanation | dict | None = None
    candidate_name: str | None = None
    candidate_summary: str | None = None
    recruiter_feedback: str | None = None

    model_config = {"from_attributes": True}

class MatchTriggerResponse(BaseModel):
    task_id: str
    jd_id: uuid.UUID
    message: str = "Matching triggered"

class MatchListResponse(BaseModel):
    jd_id: uuid.UUID
    total: int
    results: list[MatchResult]


# ═══════════════════════════════════════════════════════════════
#  Feedback
# ═══════════════════════════════════════════════════════════════
class FeedbackRequest(BaseModel):
    feedback: str = Field(..., pattern="^(positive|negative)$")

class FeedbackResponse(BaseModel):
    message: str = "Feedback recorded"


# ═══════════════════════════════════════════════════════════════
#  Task status
# ═══════════════════════════════════════════════════════════════
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None
