# Job-Candidate Matching Engine

An AI-powered, full-stack platform designed to intelligently ingest, score, rank, and explain matches between job descriptions and candidate profiles. Built specifically to handle large-scale recruitment processing, the system is designed to scale dynamically up to 100k+ candidates per execution run.

🚀 **Live Demo Frontend:** [https://4.213.115.86:3000](https://4.213.115.86:3000)  
⚙️ **Live API Documentation:** [http://4.213.115.86:8000/docs](http://4.213.115.86:8000/docs)  

📖 **Cloud Deployment Details:** View the [Azure Production Deployment Guide](docs/deployment/azure_production_deployment.md) for details on our current VM deployment and our strategy for scaling up via Azure managed services.

---

## 🎯 Core Features & Objectives Achieved

- **Multi-Format Document Parsing:** Ingest Jobs and Candidates via plain text, CSV, PDF, and DOCX. Powered by `PyMuPDF` and `python-docx`.
- **Intelligent Multi-Facet Scoring:** Candidates aren't just ranked by simple keyword overlap. The engine utilizes a weighting formula calculating Skill Match (40%), Experience Fit (30%), Education Alignment (10%), and Semantic Contextual Fit (20%).
- **Non-LLM Meaningful Explanations:** Generates human-readable breakdowns (Strengths, Weaknesses, and Recommendations) dynamically based on the exact scoring metrics, providing total transparency without relying on costly external LLM APIs.
- **Asynchronous Processing:** Heavy tasks like NLP parsing and vector embedding generation are offloaded to **Celery workers**, preventing API timeouts and ensuring smooth UX.
- **High-Performance Vector Search:** Utilizes **FAISS** for rapid cosine-similarity matching of dense vectors, enabling the system to pre-filter thousands of candidates in milliseconds.
- **Modern Interactive UI:** A React + Vite frontend styled with Tailwind CSS, delivering a premium, highly responsive user experience.

---

## 🧠 The Matching Approach & Architecture

Matching a candidate to a job is subjective. Our engine solves this by combining deterministic extraction with probabilistic semantic search.

### 1. Data Ingestion & Normalization
When a JD or Candidate is uploaded, the system parses the text and extracts explicit data points (Years of Experience, Education, Role Title). 
Skills are extracted and passed through a custom **Synonym Map Normalizer** (e.g., standardizing "React.js", "ReactJS", and "React" into a single canonical ID).

### 2. Embedding Generation
We use local NLP models via the `sentence-transformers` library (`all-MiniLM-L6-v2`) to generate 384-dimensional dense vectors for both specific skill sets and the overall work summary. Doing this locally ensures zero API costs and total data privacy.

### 3. The Multi-Facet Scoring Engine
For a given Job Description, candidates are ranked using a hybrid scoring algorithm:

- **Skill Match (40%):** Computes both exact Jaccard similarity (using the normalized synonym sets) and semantic vector similarity.
- **Experience Match (30%):** Calculates the ratio of the candidate's experience against the job's minimum required years. Capable of evaluating domain relevance based on the candidate's current title.
- **Education Match (10%):** A rule-based hierarchical check (e.g., a Master's degree fulfills a Bachelor's requirement, but not vice versa).
- **Contextual Fit (20%):** Calculates the cosine similarity between the Job's core requirements vector and the Candidate's work summary vector using **FAISS**.

**Critical Skill Penalty:** If a job requires specific "must-have" skills and a candidate lacks them, their final score receives a multiplicative penalty, pushing unqualified candidates to the bottom of the list.

### 4. Transparent Explanation Generator
Instead of querying an LLM (which is slow, expensive, and prone to hallucination), we built a deterministic explanation engine. It evaluates the exact thresholds crossed during the scoring phase and constructs natural language arrays detailing exactly *why* a candidate scored the way they did.

---

## 📈 Scalability: Handling 100k+ Candidates

Designing a system to rank 100,000+ candidates requires aggressive optimization to avoid out-of-memory errors and massive database bottlenecks.

### Current Implementation Bottlenecks & Solutions
1. **Compute Bottleneck:** Generating embeddings for 100k resumes synchronously would crash the API. 
   * **Solution:** Handled. Profile ingestion triggers asynchronous Celery tasks. The API returns a 202 Accepted immediately, while Celery handles the heavy NLP processing in the background.
2. **Database Lookup Bottleneck:** Comparing 100k candidate rows in PostgreSQL for every match request is highly inefficient.
   * **Solution:** Handled. We pre-compute and store embeddings in an in-memory **FAISS IndexFlatIP** store. 
3. **Matching Bottleneck:** Running the full 4-facet scoring engine on 100k candidates takes several seconds.
   * **Solution:** Handled via Pre-filtering. When a match is requested, we query FAISS to rapidly return the top 2,000 semantically relevant candidates. We then run the expensive multi-facet scoring engine *only* on those 2,000 candidates, cutting matching latency by 98%.

### Future Architectural Shifts for >1 Million Candidates
To push this architecture past 1 million candidates, we would implement the following cloud-native upgrades (detailed in the [Deployment Guide](docs/deployment/azure_production_deployment.md)):
- **Approximate Nearest Neighbors:** Migrate from FAISS `IndexFlatIP` (Exact search) to `IndexIVFFlat` or `HNSW` (Approximate search) to maintain sub-100ms vector lookups.
- **Distributed Vector DB:** Replace local FAISS files with a managed distributed vector database like Milvus or Pinecone.
- **Read Replicas:** Implement PostgreSQL read replicas specifically dedicated to the matching queries to avoid locking the primary write database during bulk candidate ingestion.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11, FastAPI, Uvicorn, Pydantic |
| Frontend | React 18, TypeScript, Tailwind CSS v4, React Query |
| Database | PostgreSQL 16 |
| Task Queue & Cache | Celery, Redis |
| AI / ML / Search | sentence-transformers, spaCy, FAISS |
| Infrastructure | Docker, docker-compose |

---

## 💻 Running the Project Locally

### Prerequisites
- Docker and Docker Compose installed.

### Quick Start
Clone the repository and run the entire stack with a single command:

```bash
docker-compose up --build -d
```

The services will be available at:
- **Frontend App:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs

### Running Tests
Unit tests comprehensively cover the matching engine, parsers, synonym maps, and explanation generator. You can run the test suite directly inside the running API container:

```bash
docker-compose exec api pytest tests/ -v
```

---

## ⚠️ Edge Case Handling & Limitations

- **Incomplete Profiles:** If a candidate has missing fields (e.g., no explicit years of experience), the parser gracefully defaults to 0 and relies more heavily on semantic contextual matching to gauge their seniority.
- **Vague Job Descriptions:** Vague JDs yield generic embeddings. To counter this, the `jd_parser` aggressively attempts to extract *any* recognizable technical keywords to build a baseline skill profile.
- **Tradeoffs:** 
  - We explicitly chose *not* to use LLMs (like GPT-4) for the explanation generation. While LLMs produce more conversational text, they introduce significant latency, token costs, and non-deterministic results. The template-based approach guarantees instant, accurate, and free explanations.
  - The FAISS index is currently rebuilt periodically by Celery. In a massive enterprise system with constant real-time uploads, a streaming vector database (like Qdrant) would replace this batch-rebuild process.
