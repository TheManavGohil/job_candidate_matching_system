"""
FastAPI application — all API endpoints for the Job-Candidate Matching Engine.
"""

import logging
import sys
from typing import Optional, List
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.config import get_settings
from api.models import (
    JobResponse, JobListItem, UploadJobResponse, JobCreate,
    CandidateResponse, CandidateListItem, UploadCandidateResponse,
    ParsedResumeResponse, CandidateBase,
    MatchResultsResponse, MatchCandidateItem, DetailedMatchResponse,
    FacetScores, MatchDetails, ExplanationResponse,
)
from api.storage.database import (
    init_db, get_db, SessionLocal,
    create_job, get_job, list_jobs, get_job_dict,
    create_candidate, get_candidate, list_candidates, get_candidate_dict,
    get_candidates_by_ids,
)
from api.storage.vector_store import vector_store
from api.storage.cache import cache_get, cache_set, invalidate_match_cache
from api.preprocessing.parsers import extract_text
from api.preprocessing.jd_parser import parse_jd
from api.preprocessing.resume_parser import parse_resume
from api.preprocessing.candidate_parser import parse_csv
from api.preprocessing.embeddings import (
    compute_skills_embedding, compute_summary_embedding,
)
from api.matching.engine import compute_match
from api.explanation.generator import generate_explanation

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing database and FAISS indexes")
    init_db()
    vector_store.load()
    yield
    logger.info("Shutting down")


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Job-Candidate Matching Engine",
    version="1.0.0",
    description="AI-powered job-candidate matching with multi-facet scoring",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper: rebuild FAISS from DB ────────────────────────────────────────────
def _rebuild_faiss_sync():
    """Synchronously rebuild FAISS indexes (used when Celery unavailable)."""
    from api.storage.database import get_all_candidates as _get_all
    db = SessionLocal()
    try:
        candidates = _get_all(db)
        if not candidates:
            vector_store.build_indexes(
                [], np.zeros((0, settings.EMBEDDING_DIM)),
                np.zeros((0, settings.EMBEDDING_DIM)),
            )
            return
        ids, skill_embs, summ_embs = [], [], []
        for c in candidates:
            d = get_candidate_dict(c)
            ids.append(d["candidate_id"])
            se = d.get("embedding_skills")
            su = d.get("embedding_summary")
            skill_embs.append(se if se is not None else np.zeros(settings.EMBEDDING_DIM, dtype=np.float32))
            summ_embs.append(su if su is not None else np.zeros(settings.EMBEDDING_DIM, dtype=np.float32))
        vector_store.build_indexes(
            ids, np.array(skill_embs, dtype=np.float32),
            np.array(summ_embs, dtype=np.float32),
        )
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
#  JOB ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/jobs/upload", response_model=UploadJobResponse)
async def upload_job(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a job description (file or text)."""
    text = None

    if file and file.filename:
        content = await file.read()
        text = extract_text(content, file.filename)
    elif raw_text:
        text = raw_text
    else:
        raise HTTPException(400, "Provide either a file or raw_text")

    # Parse JD
    try:
        parsed = parse_jd(text)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if title:
        parsed["title"] = title

    # Compute embeddings
    parsed["embedding_skills"] = compute_skills_embedding(
        parsed["required_skills"]
    ) if parsed["required_skills"] else compute_summary_embedding(text)

    parsed["embedding_summary"] = compute_summary_embedding(
        parsed["core_requirements_text"] or text
    )

    job = create_job(db, parsed)
    return UploadJobResponse(jd_id=str(job.jd_id), title=job.title)


@app.get("/api/jobs", response_model=List[JobListItem])
def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all uploaded job descriptions."""
    jobs = list_jobs(db, skip=skip, limit=limit)
    return [
        JobListItem(
            jd_id=str(j.jd_id), title=j.title, role_type=j.role_type,
            required_skills=j.required_skills or [],
            created_at=j.created_at,
        )
        for j in jobs
    ]


@app.get("/api/jobs/{jd_id}", response_model=JobResponse)
def get_job_detail(jd_id: str, db: Session = Depends(get_db)):
    """Get full details of a job description."""
    job = get_job(db, jd_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobResponse(
        jd_id=str(job.jd_id), title=job.title,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        min_years=job.min_years, role_type=job.role_type,
        core_requirements_text=job.core_requirements_text,
        created_at=job.created_at,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CANDIDATE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/candidates/upload", response_model=UploadCandidateResponse)
async def upload_candidates(
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Upload candidates via CSV or single resume (PDF/DOCX)."""
    if not file or not file.filename:
        raise HTTPException(400, "File is required")

    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        # CSV mode
        try:
            candidates_data = parse_csv(content)
        except ValueError as e:
            raise HTTPException(400, str(e))

        created_ids = []
        for cand in candidates_data:
            skills = cand.get("skills", [])
            cand["embedding_skills"] = compute_skills_embedding(skills) if skills else None
            summary = cand.get("work_summary", "")
            cand["embedding_summary"] = compute_summary_embedding(summary) if summary else None
            result = create_candidate(db, cand)
            created_ids.append(str(result.candidate_id))

        # Rebuild FAISS
        _rebuild_faiss_sync()
        invalidate_match_cache()

        return UploadCandidateResponse(
            message=f"Successfully uploaded {len(created_ids)} candidates",
            count=len(created_ids),
            candidate_ids=created_ids,
        )
    else:
        # Single resume
        try:
            text = extract_text(content, file.filename)
            parsed = parse_resume(text)
        except ValueError as e:
            raise HTTPException(400, str(e))

        cand_data = {
            "name": parsed["name"], "email": parsed["email"],
            "skills": parsed["skills"],
            "years_of_experience": parsed["years_of_experience"],
            "education": parsed["education"],
            "current_title": parsed["current_title"],
            "work_summary": parsed["work_summary"],
            "raw_data": {"raw_text": parsed["raw_text"]},
        }
        cand_data["embedding_skills"] = compute_skills_embedding(
            cand_data["skills"]
        ) if cand_data["skills"] else None
        cand_data["embedding_summary"] = compute_summary_embedding(
            cand_data["work_summary"]
        ) if cand_data["work_summary"] else None

        result = create_candidate(db, cand_data)
        _rebuild_faiss_sync()
        invalidate_match_cache()

        return UploadCandidateResponse(
            message="Resume parsed and candidate created",
            count=1,
            candidate_ids=[str(result.candidate_id)],
        )


@app.post("/api/candidates/parse-resume", response_model=ParsedResumeResponse)
async def parse_resume_preview(file: UploadFile = File(...)):
    """Parse a resume and return extracted fields for review (no DB save)."""
    content = await file.read()
    try:
        text = extract_text(content, file.filename)
        parsed = parse_resume(text)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return ParsedResumeResponse(
        candidate=CandidateBase(
            name=parsed["name"], email=parsed["email"],
            skills=parsed["skills"],
            years_of_experience=parsed["years_of_experience"],
            education=parsed["education"],
            current_title=parsed["current_title"],
            work_summary=parsed["work_summary"],
        ),
        raw_text=parsed["raw_text"],
        confidence=parsed.get("confidence", 1.0),
    )


@app.post("/api/candidates/confirm")
async def confirm_candidate(
    candidate: CandidateBase,
    db: Session = Depends(get_db),
):
    """Save an edited candidate profile (after resume parse review)."""
    cand_data = candidate.model_dump()
    cand_data["raw_data"] = {}
    cand_data["embedding_skills"] = compute_skills_embedding(
        cand_data["skills"]
    ) if cand_data["skills"] else None
    cand_data["embedding_summary"] = compute_summary_embedding(
        cand_data["work_summary"]
    ) if cand_data.get("work_summary") else None

    result = create_candidate(db, cand_data)
    _rebuild_faiss_sync()
    invalidate_match_cache()

    return {"candidate_id": str(result.candidate_id), "message": "Candidate saved"}


@app.get("/api/candidates", response_model=List[CandidateListItem])
def get_candidates_list(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
):
    """List all candidates."""
    cands = list_candidates(db, skip=skip, limit=limit)
    return [
        CandidateListItem(
            candidate_id=str(c.candidate_id), name=c.name, email=c.email,
            current_title=c.current_title, skills=c.skills or [],
            years_of_experience=c.years_of_experience,
            created_at=c.created_at,
        )
        for c in cands
    ]


@app.get("/api/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate_detail(candidate_id: str, db: Session = Depends(get_db)):
    """Get full candidate profile."""
    cand = get_candidate(db, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")
    return CandidateResponse(
        candidate_id=str(cand.candidate_id), name=cand.name, email=cand.email,
        skills=cand.skills or [],
        years_of_experience=cand.years_of_experience,
        education=cand.education, current_title=cand.current_title,
        work_summary=cand.work_summary, raw_data=cand.raw_data,
        created_at=cand.created_at,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  MATCHING ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/match/{jd_id}", response_model=MatchResultsResponse)
def match_candidates(
    jd_id: str,
    top_k: int = Query(50, ge=1, le=500),
    threshold: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """Run matching for a JD — returns ranked candidates."""
    # Check cache
    cache_key = f"match:{jd_id}:{top_k}:{threshold}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    job = get_job(db, jd_id)
    if not job:
        raise HTTPException(404, "Job not found")
    jd_dict = get_job_dict(job)

    # Stage 1: FAISS pre-filter
    jd_summary_emb = jd_dict.get("embedding_summary")
    if jd_summary_emb is None:
        jd_summary_emb = jd_dict.get("embedding_skills")
    if jd_summary_emb is None:
        raise HTTPException(400, "Job has no embeddings — re-upload")

    prefetch_k = max(settings.FAISS_PREFETCH_K, 2 * top_k)
    faiss_results = vector_store.search_summary(jd_summary_emb, top_k=prefetch_k)

    if not faiss_results:
        return MatchResultsResponse(jd_id=jd_id, total_candidates=0, candidates=[])

    candidate_ids = [cid for cid, _ in faiss_results]

    # Stage 2: Full scoring
    db_candidates = get_candidates_by_ids(db, candidate_ids)
    cand_map = {str(c.candidate_id): c for c in db_candidates}

    scored = []
    for cid in candidate_ids:
        if cid not in cand_map:
            continue
        cand_dict = get_candidate_dict(cand_map[cid])
        match_result = compute_match(jd_dict, cand_dict)

        if match_result["total_score"] >= threshold:
            scored.append({
                "candidate_id": cid,
                "name": cand_dict.get("name"),
                "total_score": match_result["total_score"],
                "label": match_result["label"],
                "short_summary": match_result["short_summary"],
                "top_skills": match_result["details"]["matched_skills"][:3],
            })

    # Stage 3: Sort and limit
    scored.sort(key=lambda x: x["total_score"], reverse=True)
    scored = scored[:top_k]

    result = MatchResultsResponse(
        jd_id=jd_id,
        total_candidates=len(scored),
        candidates=[MatchCandidateItem(**s) for s in scored],
    )

    cache_set(cache_key, result, ttl=settings.MATCH_CACHE_TTL)
    return result


@app.get("/api/match/{jd_id}/{candidate_id}", response_model=DetailedMatchResponse)
def match_detail(jd_id: str, candidate_id: str, db: Session = Depends(get_db)):
    """Get detailed match breakdown for a specific JD-candidate pair."""
    job = get_job(db, jd_id)
    if not job:
        raise HTTPException(404, "Job not found")
    cand = get_candidate(db, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")

    jd_dict = get_job_dict(job)
    cand_dict = get_candidate_dict(cand)
    match_result = compute_match(jd_dict, cand_dict)
    explanation = generate_explanation(match_result, jd_dict, cand_dict)

    return DetailedMatchResponse(
        jd_id=jd_id, candidate_id=candidate_id,
        candidate=CandidateResponse(
            candidate_id=str(cand.candidate_id), name=cand.name,
            email=cand.email, skills=cand.skills or [],
            years_of_experience=cand.years_of_experience,
            education=cand.education, current_title=cand.current_title,
            work_summary=cand.work_summary, raw_data=cand.raw_data,
            created_at=cand.created_at,
        ),
        total_score=match_result["total_score"],
        label=match_result["label"],
        facet_scores=FacetScores(**match_result["facet_scores"]),
        details=MatchDetails(**match_result["details"]),
        explanation=ExplanationResponse(**explanation),
    )


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "faiss_candidates": vector_store.skill_index.ntotal if vector_store.skill_index else 0,
    }
