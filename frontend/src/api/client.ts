import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Types ───────────────────────────────────────────────────────────────────

export interface Job {
  jd_id: string;
  title: string | null;
  role_type: string | null;
  required_skills: string[];
  preferred_skills: string[];
  min_years: number | null;
  core_requirements_text: string | null;
  created_at: string | null;
}

export interface Candidate {
  candidate_id: string;
  name: string | null;
  email: string | null;
  skills: string[];
  years_of_experience: number | null;
  education: string | null;
  current_title: string | null;
  work_summary: string | null;
  raw_data: Record<string, unknown> | null;
  created_at: string | null;
}

export interface MatchCandidate {
  candidate_id: string;
  name: string | null;
  total_score: number;
  label: string;
  short_summary: string;
  top_skills: string[];
}

export interface MatchResults {
  jd_id: string;
  total_candidates: number;
  candidates: MatchCandidate[];
}

export interface FacetScores {
  skill_match: number;
  experience_match: number;
  education_match: number;
  contextual_fit: number;
}

export interface MatchDetails {
  matched_skills: string[];
  missing_skills: string[];
  extra_skills: string[];
  years_score: number;
  role_score: number;
  domain_score: number;
  education_level_required: string | null;
  education_level_candidate: string | null;
}

export interface Explanation {
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
}

export interface DetailedMatch {
  jd_id: string;
  candidate_id: string;
  candidate: Candidate;
  total_score: number;
  label: string;
  facet_scores: FacetScores;
  details: MatchDetails;
  explanation: Explanation;
}

export interface ParsedResume {
  candidate: {
    name: string | null;
    email: string | null;
    skills: string[];
    years_of_experience: number | null;
    education: string | null;
    current_title: string | null;
    work_summary: string | null;
  };
  raw_text: string;
  confidence: number;
}

// ── API Functions ───────────────────────────────────────────────────────────

export async function fetchJobs(): Promise<Job[]> {
  const { data } = await api.get('/jobs');
  return data;
}

export async function fetchJob(jdId: string): Promise<Job> {
  const { data } = await api.get(`/jobs/${jdId}`);
  return data;
}

export async function uploadJob(formData: FormData) {
  const { data } = await api.post('/jobs/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function fetchCandidates(): Promise<Candidate[]> {
  const { data } = await api.get('/candidates');
  return data;
}

export async function fetchCandidate(id: string): Promise<Candidate> {
  const { data } = await api.get(`/candidates/${id}`);
  return data;
}

export async function uploadCandidates(formData: FormData) {
  const { data } = await api.post('/candidates/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function parseResume(formData: FormData): Promise<ParsedResume> {
  const { data } = await api.post('/candidates/parse-resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function confirmCandidate(candidate: ParsedResume['candidate']) {
  const { data } = await api.post('/candidates/confirm', candidate);
  return data;
}

export async function fetchMatchResults(
  jdId: string, topK = 50, threshold = 0
): Promise<MatchResults> {
  const { data } = await api.get(`/match/${jdId}`, {
    params: { top_k: topK, threshold },
  });
  return data;
}

export async function fetchDetailedMatch(
  jdId: string, candidateId: string
): Promise<DetailedMatch> {
  const { data } = await api.get(`/match/${jdId}/${candidateId}`);
  return data;
}

export async function fetchHealth() {
  const { data } = await api.get('/health');
  return data;
}

export default api;
