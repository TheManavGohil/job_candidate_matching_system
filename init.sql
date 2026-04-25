-- Initialize PostgreSQL database for Job-Candidate Matching Engine

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    jd_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    raw_text TEXT NOT NULL,
    required_skills TEXT[] DEFAULT '{}',
    preferred_skills TEXT[] DEFAULT '{}',
    min_years FLOAT,
    role_type TEXT,
    core_requirements_text TEXT,
    embedding_skills TEXT,
    embedding_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    email TEXT UNIQUE,
    raw_data JSONB,
    skills TEXT[] DEFAULT '{}',
    years_of_experience FLOAT,
    education TEXT,
    current_title TEXT,
    work_summary TEXT,
    embedding_skills TEXT,
    embedding_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates USING GIN(skills);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_candidates_created ON candidates(created_at DESC);
