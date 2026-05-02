FROM python:3.11-slim-bookworm

WORKDIR /app

# System deps for psycopg2, pdfplumber, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Pre-download the sentence-transformers embedding model so it's cached
# and never needs network access at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Run offline – model is already cached in the image
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

EXPOSE 8000

CMD ["uvicorn", "main.web:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
