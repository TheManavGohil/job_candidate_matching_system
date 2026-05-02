# Complete Production‑Ready Specification for Cursor: Explainable Job‑Candidate Matching Engine

You are to build a full‑stack, production‑grade system that ranks candidates for job descriptions and explains the reasoning in plain, powerful language. The system is designed as a set of microservices, deployable to **Azure Container Apps** (or AKS) with a single command. The matching is transparent, LLM‑powered, and utterly explainable.

Every detail below is mandatory. There are no placeholders.  
When the specification asks for a “field”, you produce it.  
When it asks for a “collection schema”, you write the exact Python/Pydantic/JSON.  
The entire codebase must be generated in the same structure that would pass a rigorous production review.

---

## 1. Project Overview

**Goal:** Build a REST API and embeddable React frontend that:

1. Ingest Job Descriptions (PDF/DOCX/text) and Candidate profiles (PDF/DOCX/CSV).  
2. Normalise both into a strict, multi‑section JSON.  
3. Let companies adjust weights per section.  
4. Match candidates to JDs using section‑wise semantic similarity.  
5. Generate rich, evidence‑backed XAI explanations using an LLM.  
6. Expose everything as a multi‑tenant API, with a plugin/embeddable frontend.

**Scale Target:** 100k candidates, sub‑second retrieval, <3 seconds end‑to‑end.

---

## 2. Technology Stack (Exact Versions)

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11 |
| Web framework | FastAPI | 0.111+ |
| ASGI server | Uvicorn | 0.30+ |
| Background tasks | Celery | 5.4+ |
| Message broker | Redis | 7+ |
| Cache | Redis | same instance |
| Database | PostgreSQL | 16 |
| Vector database | Qdrant (self‑hosted) | 1.12+ |
| Embeddings | sentence‑transformers | 2.7+ |
| PDF parsing | LlamaParse (llama-cloud) | latest |
| DOCX parsing | python‑docx | 1.1+ |
| NLP/NER | spaCy | 3.8+ |
| LLM provider | Groq (llama-3.1-70b-versatile) | via `groq` 0.13+ |
| Frontend | Next.js 14 (App Router) | 14+ |
| Styling | Tailwind CSS, shadcn/ui | latest |
| Containerisation | Docker, docker‑compose, Azure Container Apps | – |

---

## 3. Microservices Architecture

The application is split into the following services, each in its own Docker container:

1. **`api`** – FastAPI web server (handles all HTTP endpoints, synchronous logic).  
2. **`worker`** – Celery worker (asynchronous tasks: parsing, standardisation, embedding, LLM calls).  
3. **`redis`** – Redis (broker + cache).  
4. **`db`** – PostgreSQL with pgvector extension.  
5. **`qdrant`** – Qdrant vector database.  
6. **`frontend`** – Next.js server (or static export) for the embeddable UI.

All services communicate over a Docker network. For Azure, we deploy them as Azure Container Apps with managed identities.

---

## 4. Database & Storage Schemas

### 4.1 PostgreSQL Tables

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Companies (for multi‑tenancy)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(24), 'hex'),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Job Descriptions (standardised)
CREATE TABLE job_descriptions (
    jd_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    raw_text TEXT,
    standardised_json JSONB NOT NULL,
    weights JSONB NOT NULL,            -- section weights
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Candidates (standardised)
CREATE TABLE candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    email_hash TEXT,                    -- SHA256 for dedup
    raw_text TEXT,
    standardised_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_candidates_email_hash ON candidates(email_hash);
CREATE INDEX idx_candidates_company ON candidates(company_id);

-- Match results & feedback
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jd_id UUID REFERENCES job_descriptions(jd_id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    total_score FLOAT NOT NULL,
    section_scores JSONB NOT NULL,       -- per-section cos sims
    xai_explanation JSONB,               -- LLM generated
    recruiter_feedback TEXT,              -- 'positive', 'negative', null
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX idx_match_unique ON matches(jd_id, candidate_id);
```

### 4.2 Qdrant Collections

We use **two collections** per company (or global if no multi‑tenancy, but we design for multi‑tenancy with `company_id` in payload).  
Collections: `jd_sections`, `candidate_sections`.

Each collection uses vector size 384 (for MiniLM) and cosine distance.

**Points in `jd_sections`:**
- `id`: `<jd_id>_<section_name>` (e.g., `123e4567_required_skills`)
- `vector`: embedding of `section.text`
- `payload`:
  ```json
  {
    "company_id": "uuid",
    "jd_id": "uuid",
    "section": "required_skills",
    "text": "original section text"
  }
  ```

**Points in `candidate_sections`:**
- `id`: `<candidate_id>_<section_name>`
- `vector`: embedding of `section.text`
- `payload`:
  ```json
  {
    "company_id": "uuid",
    "candidate_id": "uuid",
    "section": "skills",
    "text": "Python, LLMs, ..."
  }
  ```

This enables exact section‑wise search: match JD `required_skills` against candidate `skills`, JD `responsibilities` against candidate `experience` + `projects`, etc.

---

## 5. API Endpoints (FastAPI)

All endpoints are prefixed with `/api/v1`. Multi‑tenancy is handled via header `X-API-Key` to identify company.

### 5.1 Company Management (internal)
- `POST /api/v1/companies` – create a new company, returns `api_key`.

### 5.2 Job Descriptions
- `POST /api/v1/jobs/upload` – upload file or text. Returns `{ jd_id, standardised_json }`.
- `PUT /api/v1/jobs/{jd_id}/weights` – body `{ "weights": { ... } }`. Updates weights.
- `GET /api/v1/jobs/{jd_id}` – returns full JD with weights.

### 5.3 Candidates
- `POST /api/v1/candidates/upload` – multipart: file (CSV, PDF, DOCX) or JSON array. Returns list of `candidate_id`s.
- `GET /api/v1/candidates/{candidate_id}` – returns standardised profile.

### 5.4 Matching
- `POST /api/v1/match/{jd_id}` – triggers async matching. Returns `task_id`.
- `GET /api/v1/match/{jd_id}?top_k=50&threshold=60` – returns cached match results.
- `GET /api/v1/match/{jd_id}/{candidate_id}` – returns full XAI explanation + scores.

### 5.5 Feedback
- `POST /api/v1/match/{jd_id}/{candidate_id}/feedback` – body `{ "feedback": "positive" | "negative" }`.

### 5.6 Plugin SDK
- `GET /api/v1/sdk/widget.js` – returns a small JavaScript snippet that loads the React widget.
- `GET /api/v1/sdk/ui` – serves the standalone React app (if embedded via iframe).

---

## 6. Implementation Details – Microservice Logic

### 6.1 `worker` – Asynchronous Tasks

All heavy lifting goes through Celery tasks, triggered by the API.

#### **Task: `process_job_description(jd_id, file_bytes, filename, company_id)`**
1. Extract raw text:
   - If PDF: call LlamaParse API (using `LLAMA_CLOUD_API_KEY`).  
   - If DOCX: `python-docx` to extract paragraphs.  
   - If TXT: read directly.
2. Run NER / section splitting:
   - Use spaCy to tokenise, identify headings like “Skills”, “Responsibilities”, “Qualifications”. Split text accordingly.
   - Extract initial `required_skills` items via regex + skill taxonomy file (`skill_taxonomy.json` – contain ~5000 tech skills).
3. LLM standardisation:
   - Construct prompt (see Appendix A) with the raw text and whatever was extracted.
   - Call Groq (or vLLM) to return a **valid, structured JSON** matching the JD schema, with `evidence` fields.
   - Validate the JSON; if invalid, retry once.
4. Store:
   - Insert into `job_descriptions` with `weights` set to default (equal distribution).
   - Embed each section’s `text` with `all-MiniLM-L6-v2` (locally, no API call) and upsert into Qdrant `jd_sections` collection.
5. Return `jd_id`.

#### **Task: `process_candidate(candidate_id, file_bytes, filename, company_id)`**
1. Extract raw text via LlamaParse (PDF/DOCX) or CSV mapping.
2. For CSV: map columns heuristically (match column names to “skills”, “experience”, “education”, etc.). Build raw text from all columns.
3. NER: extract name, email, phone (store but never embed) and strip them from work sections.
4. Section identification: similar heading‑based splitting.
5. LLM standardisation: construct prompt (Appendix B) to get structured candidate JSON.
6. Store:
   - Insert into `candidates`.
   - Embed each section and upsert into Qdrant `candidate_sections`.

#### **Task: `compute_matches_for_jd(jd_id, company_id, top_k=200)`**
1. Load JD from DB and Qdrant (get all section vectors).
2. For each weighted section in JD, perform a Qdrant search against the corresponding candidate section collection:
   - Map JD section → candidate section:  
     `required_skills` → `skills`,  
     `preferred_skills` → `skills`,  
     `responsibilities` → `experience` + `projects` (combine scores by max or weighted sum),  
     `qualifications` → `education` + `experience` (years sub‑field),  
     `context` → `experience` (text similarity).
   - Get top `retrieval_k=500` candidates per section with payload (candidate_id).
3. Reciprocal Rank Fusion:
   - For each candidate, compute RRF score: `sum(1 / (60 + rank_section_i))`.
   - Keep top `top_k * 2` candidates.
4. For each candidate in the merged pool:
   - Retrieve all section embeddings from Qdrant (pre‑computed, cached).
   - Compute final score = sum(section_weight * cosine_similarity(JD_emb, candidate_emb)).
   - Store in `matches` table (insert or update).
5. Generate XAI explanations for top 50 candidates (or top_k):
   - For each candidate, call `generate_explanation` task (celery chain).
6. Cache full results in Redis (`match:jd_id`) with TTL 1 hour.

#### **Task: `generate_explanation(jd_id, candidate_id)`**
1. Fetch JD and candidate standardised JSON.
2. Fetch per‑section cosine similarities from `matches`.
3. Construct LLM prompt (Appendix C) requiring evidence‑based strengths/weaknesses.
4. Call Groq, parse JSON output.
5. Update `matches.xai_explanation` with the LLM response.

---

## 7. Matching Algorithm – Detailed Mathematics

Given JD sections \(S_{jd} = \{s_1, s_2, ..., s_k\}\) with weights \(w_i\) and corresponding candidate sections \(S_{cand}\), we define:

\[
\text{score} = \sum_{i=1}^{k} w_i \cdot \text{cos\_sim}(e_{jd}^{s_i}, e_{cand}^{s_i})
\]

Where \(e\) is the 384‑dim embedding produced by `all-MiniLM-L6-v2`. Cosine similarity is computed via Qdrant (or directly if vectors are fetched). All similarities are in \([-1,1]\); we clip negatives to 0.

Weights are normalised to sum to 100 internally. The company can adjust them; the UI shows sliders from 0 to 100, and the backend normalises.

Example mapping for an AI Engineer JD:

| JD Section | Weight | Candidate Section(s) | Similarity |
|------------|--------|----------------------|------------|
| `required_skills` | 30 | `skills` | `cos_sim()` |
| `preferred_skills` | 10 | `skills` | `cos_sim()` |
| `responsibilities` | 25 | `experience` + `projects` (text concat) | `max(cos_sim(exp), cos_sim(proj))` |
| `qualifications` | 20 | `education` + `experience` (years match bonus) | 0.7*cos_sim(edu) + 0.3*years_match |
| `context` | 15 | `experience` (summary) | `cos_sim()` |

The `years_match` is a simple piecewise function: if `candidate_years >= jd_min_years` then 1, else `candidate_years / jd_min_years`.

All these rules are configurable via the company settings JSON.

---

## 8. XAI Explanation Prompt (Appendix C)

```
You are an expert recruiter. Given a job description and a candidate profile, 
evaluate the match. Use the provided per‑section similarity scores to ground your assessment.

You must output a JSON object with the following structure, 
and nothing else (no markdown, no extra text):

{
  "overall_grade": "Strong Match" | "Good Fit" | "Potential" | "Not Recommended",
  "strengths": [
    {
      "point": "string explaining strength",
      "evidence": "exact quote from candidate profile"
    }
  ],
  "weaknesses": [
    {
      "point": "string explaining weakness",
      "evidence": "missing or low similarity area reference"
    }
  ],
  "recommendation": "1-2 sentence summary"
}
```

---

## 9. Frontend: Embeddable Next.js Application

The frontend is built as a Next.js 14 App Router app with the following pages:

- `/login` – simple company login via API key.
- `/dashboard` – show uploaded JDs, upload new.
- `/jobs/[jd_id]` – view JD, adjust weights (sliders), trigger match, see results.
- `/candidates` – upload and list candidates.
- `/match/[jd_id]` – ranked results with cards showing score, grade, top strengths.
- `/match/[jd_id]/[candidate_id]` – full XAI explanation, per‑section scores.

**Plugin mode:**  
The entire app can be rendered as a widget inside an iframe or via a custom element. To enable this, the main layout detects if it’s embedded via `window !== parent` and hides navigation, leaving only the core pages. A simple JavaScript snippet (`widget.js`) can be injected into the host site to mount the widget.

The widget SDK is served from the API itself. For example:
```html
<script src="https://api.example.com/api/v1/sdk/widget.js" data-company-api-key="abc123"></script>
<div id="match-widget"></div>
```

---

## 10. Azure Deployment Configuration

### 10.1 Dockerfiles

**`Dockerfile.api`**  
```dockerfile
FROM python:3.11-slim-bookworm
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ .
CMD ["uvicorn", "main.web:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`Dockerfile.worker`** – same image, entrypoint:  
```dockerfile
CMD ["celery", "-A", "main.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
```

**`Dockerfile.frontend`** – standard Next.js build with `output: 'standalone'`.

### 10.2 Azure Container Apps

Create an Azure Container App Environment and deploy four container apps:

- `api` – HTTP ingress on port 8000, scale 0‑10.  
- `worker` – no ingress, scale 0‑5.  
- `frontend` – HTTP ingress on port 3000, scale 0‑3.  
- `qdrant` – (or use Qdrant Cloud), but self‑hosted can be a container app with persistent storage.

Use **Azure Cache for Redis** and **Azure Database for PostgreSQL** managed services, connected via environment variables.

### 10.3 Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_URL` | Qdrant endpoint |
| `QDRANT_API_KEY` | (if cloud) |
| `LLAMA_CLOUD_API_KEY` | LlamaParse API key |
| `GROQ_API_KEY` | Groq API key |
| `JWT_SECRET` | For company authentication |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |
| `MAX_CANDIDATES_RETRIEVAL` | 500 |

---

## 11. Code Structure

The monorepo is organised as:

```
/
├── api/
│   ├── main/
│   │   ├── web.py                 # FastAPI app instance
│   │   ├── celery_app.py          # Celery instance
│   │   ├── config.py              # Settings from env
│   │   ├── models/                # Pydantic schemas & DB models
│   │   ├── routes/                # API endpoints
│   │   ├── tasks/                 # Celery task definitions
│   │   ├── services/              # Business logic
│   │   │   ├── parsing.py         # LlamaParse, spaCy
│   │   │   ├── standardisation.py # LLM completion prompts
│   │   │   ├── embeddings.py      # sentence‑transformers
│   │   │   ├── qdrant_client.py   # Qdrant operations
│   │   │   ├── matching.py        # Core matching engine
│   │   │   ├── xai.py             # Explanation generation
│   │   │   └── sdk.py             # Plugin SDK endpoint
│   │   ├── db.py                  # SQLAlchemy setup
│   │   └── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                       # Next.js App Router
│   ├── components/                # UI components
│   ├── lib/                       # API client, types
│   └── ...
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

---

## 12. Implementation Steps for Cursor

Generate all files in the order below, ensuring they are complete and error‑free.

1. **Root config files:** `.env.example`, `docker-compose.yml`, `README.md`.  
2. **API skeleton:** `api/main/config.py`, `api/main/web.py`, `api/main/celery_app.py`, `api/main/db.py`.  
3. **Models:** Pydantic schemas for JD, Candidate, Match, Company, Weights.  
4. **Routes:** all endpoints as per Section 5.  
5. **Services – Parsing:** `parsing.py` implementing LlamaParse and spaCy section splitting.  
6. **Services – Standardisation:** prompts for JD and candidate, Groq call with retry.  
7. **Services – Embeddings:** local `SentenceTransformer` wrapper with caching.  
8. **Services – Qdrant:** client init, upsert, search by section.  
9. **Services – Matching:** core scoring logic, reciprocal rank fusion, section mapping.  
10. **Services – XAI:** explanation prompt and storage.  
11. **Services – SDK:** widget endpoint serving a simple JavaScript snippet.  
12. **Tasks:** Celery task definitions wiring services.  
13. **Frontend:** Next.js pages, components, Tailwind config, shadcn/ui setup.  
14. **Dockerfiles** and production compose file.  

After generation, run `docker-compose up` and everything must work.

**Now build the application exactly as specified. No missing pieces.**