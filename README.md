# Job-Candidate Matching Engine

An AI-powered, full-stack application that matches candidates to job descriptions using multi-facet scoring with semantic embeddings. Built for production scale (100k+ candidates).

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌───────────┐
│   React UI   │────▶│  FastAPI API  │────▶│ PostgreSQL│
│  (Vite + TS) │     │              │     └───────────┘
└──────────────┘     │              │────▶┌───────────┐
                     │              │     │   Redis   │
                     │              │     └───────────┘
                     │              │────▶┌───────────┐
                     └──────────────┘     │   FAISS   │
                           │              └───────────┘
                     ┌─────┴──────┐
                     │   Celery   │
                     │   Worker   │
                     └────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Frontend | React 18, TypeScript, Tailwind CSS v4, React Query |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Vector Search | FAISS (IndexFlatIP) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2, 384d) |
| NLP | spaCy (en_core_web_sm) |
| Task Queue | Celery + Redis |
| Infrastructure | Docker, docker-compose |

## Quick Start

### With Docker (recommended)

```bash
docker-compose up --build
```

Services:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
# Install Python dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Start PostgreSQL and Redis (or use Docker for these)
docker-compose up db redis -d

# Run API
uvicorn api.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Matching Approach

### Multi-Facet Scoring (0-100)

| Facet | Weight | Method |
|-------|--------|--------|
| Skill Match | 40% | Jaccard overlap + semantic embedding similarity |
| Experience Match | 30% | Years ratio + role title alignment + domain relevance |
| Education Match | 10% | Degree level comparison |
| Contextual Fit | 20% | Full-text embedding cosine similarity |

### Pipeline

1. **Upload JD** → parse skills, requirements, compute embeddings
2. **Upload Candidates** → parse profiles, compute embeddings, build FAISS index
3. **Match** → FAISS pre-filter (top 2000) → full scoring → rank → explain

### Critical Skill Penalty

Each missing "must-have" skill reduces the final score by 10% multiplicatively.

### Explanation Generation

Template-based (no LLM) — produces:
- **Strengths**: matched skills, experience fit, domain relevance
- **Weaknesses**: skill gaps, experience gaps, education mismatch
- **Recommendation**: classification with hiring advice

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs/upload` | Upload JD (file or text) |
| GET | `/api/jobs` | List all jobs |
| GET | `/api/jobs/{jd_id}` | Job details |
| POST | `/api/candidates/upload` | Upload CSV or resume |
| POST | `/api/candidates/parse-resume` | Parse resume (preview) |
| POST | `/api/candidates/confirm` | Save edited candidate |
| GET | `/api/candidates` | List candidates |
| GET | `/api/candidates/{id}` | Candidate details |
| GET | `/api/match/{jd_id}` | Run matching |
| GET | `/api/match/{jd_id}/{cand_id}` | Detailed match breakdown |
| GET | `/api/health` | Health check |

## Scaling to 100k Candidates

### Current Implementation
- FAISS `IndexFlatIP` for vector search (exact, fast for <100k)
- Redis caching of match results per JD
- PostgreSQL with GIN indexes on skills arrays
- Synchronous matching with FAISS pre-filter → 2000 candidates → full scoring

### Scaling Strategy
- **FAISS**: Switch to `IndexIVFFlat` or `HNSW` for approximate search
- **Compute**: Multiple Celery workers for parallel embedding computation
- **Database**: Read replicas for candidate lookups
- **API**: Multiple Uvicorn instances behind Nginx load balancer
- **Cache**: Redis cluster, pre-compute candidate skill sets for fast intersection

### Future Improvements
- GPU-accelerated embedding computation for batch ingest
- Milvus or Weaviate for vector storage beyond 1M candidates
- Separate matching microservice for independent scaling
- Real-time index updates via streaming pipeline

## Testing

```bash
cd /path/to/project
pytest tests/ -v
```

## Trade-offs

| Decision | Rationale |
|----------|-----------|
| FAISS over pgvector | Faster in-memory search, better for high-throughput matching |
| Pickle for Redis cache | Faster serialization of numpy arrays vs JSON |
| Synchronous matching | Simpler architecture; FAISS pre-filter keeps latency low |
| Template-based explanations | Deterministic, fast, no API costs; LLM can be added later |
| Embedding averaging for skills | Simple but effective; weighted averaging is a future improvement |

## Project Structure

```
├── api/
│   ├── main.py                     # FastAPI endpoints
│   ├── models.py                   # Pydantic schemas
│   ├── config.py                   # Environment config
│   ├── tasks.py                    # Celery tasks
│   ├── preprocessing/
│   │   ├── jd_parser.py            # Job description parsing
│   │   ├── resume_parser.py        # Resume parsing (spaCy + regex)
│   │   ├── candidate_parser.py     # CSV parsing
│   │   ├── embeddings.py           # Sentence-transformer wrapper
│   │   └── parsers.py              # PDF/DOCX text extraction
│   ├── matching/
│   │   ├── engine.py               # Multi-facet scoring engine
│   │   └── weights.py              # Configurable weights
│   ├── explanation/
│   │   └── generator.py            # Template-based explanations
│   ├── storage/
│   │   ├── database.py             # PostgreSQL CRUD
│   │   ├── vector_store.py         # FAISS wrapper
│   │   └── cache.py                # Redis caching
│   └── utils/
│       └── synonym_map.py          # Skill normalization
├── frontend/                       # React + TypeScript + Tailwind
├── tests/                          # Unit tests
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.frontend
├── init.sql
└── requirements.txt
```
