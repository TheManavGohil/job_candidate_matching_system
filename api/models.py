"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# ── Job Schemas ──────────────────────────────────────────────────────────────

class JobBase(BaseModel):
    title: Optional[str] = None
    raw_text: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years: Optional[float] = None
    role_type: Optional[str] = None
    core_requirements_text: Optional[str] = None


class JobCreate(BaseModel):
    """For JSON-based job upload."""
    raw_text: str
    title: Optional[str] = None


class JobResponse(BaseModel):
    jd_id: str
    title: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years: Optional[float] = None
    role_type: Optional[str] = None
    core_requirements_text: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListItem(BaseModel):
    jd_id: str
    title: Optional[str] = None
    role_type: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


# ── Candidate Schemas ────────────────────────────────────────────────────────

class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    education: Optional[str] = None
    current_title: Optional[str] = None
    work_summary: Optional[str] = None


class CandidateResponse(CandidateBase):
    candidate_id: str
    raw_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateListItem(BaseModel):
    candidate_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    current_title: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    created_at: Optional[datetime] = None


# ── Match Schemas ────────────────────────────────────────────────────────────

class MatchCandidateItem(BaseModel):
    candidate_id: str
    name: Optional[str] = None
    total_score: float
    label: str
    short_summary: str
    top_skills: List[str] = Field(default_factory=list)


class MatchResultsResponse(BaseModel):
    jd_id: str
    total_candidates: int
    candidates: List[MatchCandidateItem]


class FacetScores(BaseModel):
    skill_match: float
    experience_match: float
    education_match: float
    contextual_fit: float


class MatchDetails(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    extra_skills: List[str] = Field(default_factory=list)
    years_score: float = 0.0
    role_score: float = 0.0
    domain_score: float = 0.0
    education_level_required: Optional[str] = None
    education_level_candidate: Optional[str] = None


class ExplanationResponse(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendation: str = ""


class DetailedMatchResponse(BaseModel):
    jd_id: str
    candidate_id: str
    candidate: CandidateResponse
    total_score: float
    label: str
    facet_scores: FacetScores
    details: MatchDetails
    explanation: ExplanationResponse


# ── Upload Responses ─────────────────────────────────────────────────────────

class UploadJobResponse(BaseModel):
    jd_id: str
    title: Optional[str] = None
    message: str = "Job description uploaded successfully"


class UploadCandidateResponse(BaseModel):
    message: str
    count: int = 0
    candidate_ids: List[str] = Field(default_factory=list)


class ParsedResumeResponse(BaseModel):
    """Returned after resume parse so user can review before final submit."""
    candidate: CandidateBase
    raw_text: str
    confidence: float = 1.0


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    result: Optional[Any] = None
