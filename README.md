# Job-Candidate Matching Engine

> An Explainable AI-powered candidate ranking system with section-wise semantic matching, asynchronous processing, and a full-stack web interface.

---

## Table of Contents

1. [Matching Approach](#matching-approach)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack & Design Decisions](#tech-stack--design-decisions)
4. [System Workflow](#system-workflow)
5. [API Endpoints](#api-endpoints)
6. [Explainability (XAI)](#explainability-xai)
7. [Edge Case Handling](#edge-case-handling)
8. [Scalability to 100k Candidates](#scalability-to-100k-candidates)
9. [Deployment](#deployment)
10. [Running Locally](#running-locally)
11. [Environment Variables](#environment-variables)
12. [Tradeoffs & Limitations](#tradeoffs--limitations)

---

## Matching Approach

The core philosophy is **Section-Wise Semantic Matching with Reciprocal Rank Fusion (RRF)**, not simple keyword overlap.

### Why Section-Wise?

A resume is not a single blob of text. It has discrete sections with different semantic meanings: Skills, Experience, Education, Projects. A JD similarly has Required Skills, Preferred Skills, Responsibilities, and Qualifications.

Matching the entire resume against the entire JD produces diluted, inaccurate signals. For example, a candidate might mention "Python" in a tiny personal project but have zero professional Python experience — a whole-document match would score them too high.

By splitting both the JD and the resume into sections and matching **JD sections against the corresponding candidate sections**, the engine achieves far higher precision:

| JD Section | Matched Against Candidate Section(s) |
|---|---|
| `required_skills` | `skills` |
| `preferred_skills` | `skills` |
| `responsibilities` | `experience`, `projects` (max score wins) |
| `qualifications` | `education`, `experience` |
| `context` | `experience` |

### Why Semantic (Vector) Matching, Not Keyword Overlap?

Keyword overlap fails on synonyms. A JD that says "proficiency in containerisation" will not match a resume that says "experienced with Docker and Kubernetes" using keyword methods. Semantic embeddings (`all-MiniLM-L6-v2`) map both phrases to nearby vectors in 384-dimensional space, so cosine similarity correctly identifies them as semantically equivalent.

### The Algorithm: Two-Stage Pipeline

**Stage 1 — Reciprocal Rank Fusion (RRF) Shortlisting**

For each JD section vector, the engine queries Qdrant for the top-500 candidates in that section. This produces multiple ranked lists (one per section). These lists are merged using RRF:

```
RRF_score(candidate) = Σ  1 / (k + rank_in_section)
```

where `k = 60` (a standard smoothing constant that prevents the #1 ranked candidate from dominating the result entirely). RRF is rank-based, not score-based, which makes it robust to the different magnitude scales of different embedding spaces.

**Stage 2 — Weighted Scoring**

The RRF shortlist is re-ranked using the recruiter's custom weights applied to the actual cosine similarity scores:

```
final_score = Σ  (normalized_weight × section_cosine_similarity)
```

Default weights are:

| Section | Default Weight |
|---|---|
| Required Skills | 30% |
| Responsibilities | 25% |
| Qualifications | 20% |
| Context | 15% |
| Preferred Skills | 10% |

These weights are **fully configurable per JD** via the frontend's weight sliders, allowing recruiters to tune the importance of each signal for each role.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                          │
│   Upload JDs & Resumes │ Trigger Matching │ Browse Results       │
└──────────────┬──────────────────────────────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────────────────────────────┐
│                    FastAPI (Async)                                │
│   /companies  /jobs  /candidates  /match  /feedback              │
└──────┬─────────────────────────────┬────────────────────────────┘
       │ Enqueue Tasks                │ Read/Write
┌──────▼──────┐              ┌───────▼───────┐
│  Redis      │              │  PostgreSQL   │
│  (Broker)   │              │  (Relational) │
└──────┬──────┘              └───────────────┘
       │ Consume
┌──────▼──────────────────────────────────────────────────────────┐
│                    Celery Workers                                 │
│  parse → NER → LLM standardise → embed → upsert to Qdrant       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Vector Search
┌──────────────────────────▼──────────────────────────────────────┐
│              Qdrant Vector Database                               │
│  Collections: jd_sections │ candidate_sections (384-dim, HNSW)  │
└─────────────────────────────────────────────────────────────────┘
```

**Services (Docker Compose):**

| Service | Image | Purpose |
|---|---|---|
| `api` | FastAPI + Uvicorn | HTTP API server |
| `worker` | Celery | Background document processing & matching |
| `db` | PostgreSQL 16 (pgvector) | Relational data store |
| `redis` | Redis 7 | Celery message broker + match result cache |
| `qdrant` | Qdrant v1.12.1 | Vector database with HNSW index |
| `frontend` | Next.js 15 | Web UI |

---

## Tech Stack & Design Decisions

### FastAPI (not Flask or Django)

FastAPI is fully async-native, which is critical here: the API receives large file uploads, writes to PostgreSQL, and dispatches tasks — all I/O-bound operations. Async support means one Uvicorn worker can handle hundreds of concurrent upload requests without spawning threads. It also auto-generates OpenAPI docs at `/docs`.

### Celery + Redis (Async Task Queue)

Document parsing calls LlamaParse (a network call), the LLM standardisation calls Groq (another network call), and embedding a batch of resumes is CPU-heavy. Doing all of this synchronously inside a FastAPI route would cause timeouts on any real-world load. Celery decouples ingestion from processing: the API responds with `202 Accepted` immediately, and workers process in the background.

### Qdrant (not FAISS)

FAISS is a pure in-memory library. It has no built-in support for metadata filtering. In this system, every vector must be filtered by `company_id` (multi-tenancy) **and** `section_name` before similarity search. Implementing that correctly in FAISS requires building and maintaining custom index partitions per company per section — a significant engineering burden. Qdrant handles payload filtering natively with its HNSW index, is horizontally scalable, and exposes a clean Python client with an HTTP API.

### LlamaParse (not PyPDF2 / pdfplumber)

PyPDF2 and pdfplumber extract raw text by scanning PDF byte streams. They frequently scramble multi-column layouts and lose section headings. Because this system's matching precision depends entirely on correctly identifying sections (Skills vs. Experience vs. Education), a structurally-aware parser is mandatory.

LlamaParse uses vision-language models to parse PDFs into clean Markdown, preserving tables, bullet hierarchies, and headings. **`pdfplumber` is retained as an automatic fallback** if the LlamaParse API key is absent or the API call fails, ensuring the system degrades gracefully rather than crashing.

### `all-MiniLM-L6-v2` Embeddings (Local, Not OpenAI)

This 384-dimensional SentenceTransformer model runs locally inside the Docker container — zero latency to an external API, zero per-token cost. It is purpose-built for semantic similarity tasks and scores near the top of the MTEB benchmark for its size. The embedding service is loaded once at startup and cached with `@lru_cache` for the process lifetime.

### Groq LLM (`llama-3.3-70b-versatile`)

Groq's LPU (Language Processing Unit) hardware delivers ~500 tokens/second inference — roughly 10-20× faster than comparable GPU-hosted APIs. Since every match detail page generates an LLM explanation, latency here directly impacts recruiter experience. Groq keeps explanations near-instant. The model is used for two tasks: (1) **Standardisation** — converting raw resume/JD text into strict JSON schemas, and (2) **XAI** — generating evidence-backed match explanations.

### PostgreSQL with JSONB

The `standardised_json` fields on both `JobDescription` and `Candidate` tables store the LLM-extracted structured data as JSONB. JSONB columns are indexed and queryable in PostgreSQL, providing flexibility without a separate NoSQL store. The `Match` table stores `section_scores` and `xai_explanation` as JSONB as well, enabling rich filtering without schema migrations every time the explanation format evolves.

---

## System Workflow

### Ingesting a Job Description

1. Recruiter uploads a JD file (PDF, DOCX, or TXT) via the frontend.
2. FastAPI saves a placeholder `JobDescription` row to PostgreSQL and dispatches a `process_job_description` Celery task.
3. Worker picks it up:
   - Extracts text via **LlamaParse** (or `pdfplumber` fallback).
   - Cleans and splits text into sections using regex heading detection.
   - Calls **Groq** to standardise into a strict JSON schema (`title`, `required_skills`, `preferred_skills`, `responsibilities`, `qualifications`, `context`).
   - Embeds each section with `all-MiniLM-L6-v2`.
   - Upserts section vectors into the **Qdrant** `jd_sections` collection with metadata payloads (`company_id`, `section`).
   - Updates the DB row with the final `raw_text` and `standardised_json`.

### Ingesting Candidates

The same pipeline runs for candidates (individually or in bulk via CSV/XLSX batch upload). Candidate sections (`skills`, `experience`, `education`, `projects`) are embedded and stored in the `candidate_sections` Qdrant collection tagged with `company_id` and `candidate_id`.

An **email SHA-256 hash** is stored for deduplication — if a candidate uploads the same resume twice, the system updates the existing record rather than creating a duplicate.

### Triggering a Match

1. Recruiter clicks **"Run Match"** on the JD page (optionally adjusting section weights).
2. FastAPI dispatches a `compute_matches_for_jd` Celery task (`202 Accepted`).
3. Worker runs the **two-stage matching pipeline**:
   - Fetches all JD section vectors from Qdrant.
   - Per-section candidate search (top 500) → per-candidate RRF score.
   - Re-ranks shortlist with recruiter weights → final 0-100 score.
   - Persists all `Match` rows to PostgreSQL.
   - Caches the result list in Redis (TTL: 1 hour) for instant subsequent reads.
4. For each match, dispatches individual `generate_xai_explanation` tasks in parallel.

### Viewing Results

- `GET /api/v1/match/{jd_id}` reads from the Redis cache if warm, falls back to PostgreSQL.
- `GET /api/v1/match/{jd_id}/{candidate_id}` returns the full XAI breakdown for one candidate.
- The frontend merges live XAI data from PostgreSQL into cached results so explanations appear as soon as each one is ready.

---

## API Endpoints

All endpoints are under `/api/v1` and require an `X-API-Key` header.

| Method | Path | Description |
|---|---|---|
| `POST` | `/companies/register` | Register a new company & get API key |
| `POST` | `/jobs/upload` | Upload a JD file; triggers async processing |
| `GET` | `/jobs/` | List all JDs for company |
| `POST` | `/candidates/upload` | Upload a single candidate resume |
| `POST` | `/candidates/batch` | Upload CSV/XLSX batch of candidates |
| `GET` | `/candidates/` | List all candidates |
| `POST` | `/match/{jd_id}` | Trigger matching for a JD (async, returns task_id) |
| `GET` | `/match/{jd_id}` | Get ranked candidate list for a JD |
| `GET` | `/match/{jd_id}/{candidate_id}` | Get detailed XAI explanation for one match |
| `POST` | `/feedback/{jd_id}/{candidate_id}` | Submit recruiter feedback (thumbs up/down) |
| `GET` | `/api/v1/health` | Health check |

Interactive Swagger docs are available at `http://localhost:8000/docs` when running locally.

---

## Explainability (XAI)

Every match result includes a structured explanation generated by the LLM. The explanation is grounded in actual similarity scores — the LLM is given the per-section scores as numeric context so it cannot hallucinate a match.

**Example XAI Output:**

```json
{
  "overall_grade": "Strong Match",
  "strengths": [
    {
      "point": "Skills are a near-perfect fit for the role",
      "evidence": "Candidate lists Python, FastAPI, PostgreSQL, Redis — all required by the JD"
    }
  ],
  "weaknesses": [
    {
      "point": "Limited team leadership experience",
      "evidence": "Responsibilities similarity score 0.61 — JD emphasises managing cross-functional teams"
    }
  ],
  "recommendation": "Strongly recommend for a technical interview. Leadership growth area to probe."
}
```

Grades: `Strong Match` | `Good Fit` | `Potential` | `Not Recommended`

---

## Edge Case Handling

| Scenario | Handling |
|---|---|
| **Vague or minimal JD** | LLM standardisation fills in best-effort structure; missing sections produce zero weight contribution, not errors |
| **Incomplete candidate profile** | If no structured sections are extracted, raw text is embedded as a fallback so the candidate is still searchable |
| **LlamaParse API failure** | `pdfplumber` is automatically used as a synchronous fallback |
| **LLM standardisation failure** | Retried once with the error message appended to the prompt; if second attempt fails, a minimal safe schema is returned |
| **Duplicate candidate upload** | Email SHA-256 hash deduplication; existing record is updated rather than duplicated |
| **Binary/corrupted files** | `extract_text` uses `errors="replace"` UTF-8 decoding; malformed PDFs fall through to the text fallback |
| **Empty embedding text** | `embed_text` returns a zero vector for empty strings, which scores 0.0 in cosine similarity — safely excluded |
| **Celery task failure** | `max_retries=2` with a 10-second countdown backoff on all processing tasks |

---

## Scalability to 100k Candidates

The current architecture handles hundreds of candidates efficiently. Here is what changes at 100k:

### What Already Scales

- **Qdrant HNSW index:** Approximate nearest-neighbour search is sub-linear. Searching 100k vectors takes ~5ms vs. searching 1k vectors — not 100×. This is Qdrant's core strength.
- **Celery workers:** Stateless. Adding workers is a single `docker compose scale worker=N` command or a Kubernetes `HorizontalPodAutoscaler`.
- **Redis caching:** Match results are cached for 1 hour. After the first request, 100k-candidate match results are served in milliseconds.

### Bottlenecks & Required Changes

| Bottleneck | Current State | At 100k Scale |
|---|---|---|
| **Batch embedding** | Candidates embedded one-at-a-time in individual Celery tasks | Switch to batch embedding with `embed_batch()` (already implemented) called in chunks of 512; use GPU workers |
| **LLM standardisation** | One Groq API call per candidate | Parallelize with Celery `group()` across many workers; implement a rate-limit token bucket |
| **XAI generation** | One LLM call per match result shown | Generate lazily (only when recruiter opens the detail view) rather than pre-generating for all 100k |
| **PostgreSQL writes** | Sequential inserts per candidate | Use `INSERT ... ON CONFLICT` bulk upserts; add a read replica for match queries |
| **Qdrant memory** | Single node, in-memory index | Enable Qdrant's on-disk HNSW mode; shard collections across nodes using Qdrant's distributed mode |
| **Celery queue depth** | Single Redis list | Partition queues by priority: `upload_queue` (fast), `embedding_queue` (slow, GPU), `xai_queue` (rate-limited) |

### Architectural Changes for 100k+

```
Upload Service  ──►  Kafka Topic  ──►  Embedding Workers (GPU, batch)
                                   ──►  LLM Standardisation Workers
                                   ──►  Qdrant Ingest Workers

Match Request   ──►  Pre-filter in Postgres (years_experience, location)
                ──►  Vector Search in Qdrant (HNSW, filtered)
                ──►  RRF + Scoring (in-memory, fast)
                ──►  XAI (lazy, on-demand)
```

For truly massive scale (1M+), replace Redis as broker with **Kafka** for durable, partitioned message queues and introduce a dedicated **pre-filter stage** using structured metadata (years of experience, location, required certifications) in PostgreSQL before touching the vector index — reducing the ANN search space by 80-90%.

---

## Deployment

### Live Demo (Azure)
The system is currently deployed live on a Microsoft Azure Virtual Machine. You can access it here:

*   **Web Application (Frontend):** [http://98.70.35.50:3000](http://98.70.35.50:3000)
*   **API Documentation (Swagger):** [http://98.70.35.50:8000/docs](http://98.70.35.50:8000/docs)

*(Note: The deployment uses raw IP addresses, so it runs on HTTP. Ensure your browser doesn't automatically force HTTPS).*

### Azure VM Deployment Setup

The deployment uses a single VM approach with all containers managed by Docker Compose. This is the simplest production-ready configuration: one VM, one `docker compose up -d`, everything running.

**Architecture on Azure:**

```
Azure VM (Ubuntu 22.04)
├── Docker Engine
├── docker-compose.prod.yml
│   ├── api          (port 8000, public)
│   ├── worker       (internal)
│   ├── frontend     (port 3000, public)
│   ├── db           (internal only)
│   ├── redis        (internal only)
│   └── qdrant       (port 6333, internal)
└── Azure NSG rules: 80, 443, 3000, 8000 open
```

### Run with a Single Command

```bash
# Clone the repository
git clone <repo-url>
cd assignment_v2

# Copy environment file and fill in your API keys
cp .env.example .env

# Build all images and start all services
docker compose up -d --build

# The system will be available at:
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

That's it. One command starts the entire stack.

---

## Running Locally

**Prerequisites:** Docker Engine ≥ 24, Docker Compose v2

```bash
# 1. Clone
git clone <repo-url>
cd assignment_v2

# 2. Configure
cp .env.example .env
# Edit .env and set GROQ_API_KEY and LLAMA_CLOUD_API_KEY

# 3. Start
docker compose up -d --build

# 4. Register a company (get your API key)
curl -X POST http://localhost:8000/api/v1/companies/register \
  -H "Content-Type: application/json" \
  -d '{"name": "My Company"}'
# Response includes your api_key

# 5. Open the frontend
open http://localhost:3000
# Enter your api_key to log in
```

**Stopping:**
```bash
docker compose down          # Stop containers
docker compose down -v       # Stop and wipe all volumes (full reset)
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for LLM standardisation & XAI | Yes |
| `LLAMA_CLOUD_API_KEY` | LlamaParse API key for PDF parsing | No (falls back to pdfplumber) |
| `DATABASE_URL` | PostgreSQL connection string | Auto-set in Docker |
| `REDIS_URL` | Redis connection string | Auto-set in Docker |
| `QDRANT_URL` | Qdrant endpoint | Auto-set in Docker |
| `JWT_SECRET` | Secret for JWT token signing | Yes |
| `EMBEDDING_MODEL` | SentenceTransformer model name | Default: `all-MiniLM-L6-v2` |
| `LLM_MODEL` | Groq model name | Default: `llama-3.3-70b-versatile` |
| `MAX_CANDIDATES_RETRIEVAL` | Max candidates per Qdrant search | Default: `500` |

---

## Tradeoffs & Limitations

### What We Chose Not to Build (and Why)

**BM25 / Keyword Hybrid Search:** A hybrid of dense vectors + BM25 sparse retrieval (like Qdrant's own hybrid search) would improve recall for exact-match acronyms (e.g., "AWS", "GCP"). This was deprioritised in favour of getting the semantic pipeline working end-to-end with strong explainability.

**Re-ranking with a Cross-Encoder:** A cross-encoder (e.g., `ms-marco-MiniLM`) would re-rank the shortlist with better precision by jointly encoding the JD and candidate text together. It is ~10× slower than bi-encoder similarity, making it impractical at retrieval time without a dedicated re-ranking stage. This is the most impactful future improvement.

**Streaming XAI Generation:** XAI explanations are generated as a single JSON object. Streaming partial tokens to the UI (like ChatGPT's typewriter effect) would feel faster. Not implemented due to added frontend complexity.

**Authentication:** The system uses a simple API-key-per-company model. Production would require OAuth 2.0 / SSO for recruiter identity management.

### Known Limitations

- LLM standardisation quality depends on the resume being in English.
- Very short or sparse resumes (less than 100 words) produce low-quality embeddings; the system scores them low but does not explicitly flag them as incomplete.
- Qdrant runs as a single node; no replication is configured in the local Docker Compose setup.
