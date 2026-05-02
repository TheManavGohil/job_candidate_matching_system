/**
 * API client – always sends the default API key (no-auth mode).
 */

import type {
  CandidateUploadResponse,
  JobDescription,
  JDUploadResponse,
  MatchListResponse,
  MatchResult,
  MatchTriggerResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const DEFAULT_KEY =
  process.env.NEXT_PUBLIC_DEFAULT_API_KEY || "matchiq-default-key-2024";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "X-API-Key": DEFAULT_KEY,
    ...(options.headers as Record<string, string>),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json();
}

// ── Jobs ─────────────────────────────────────────────────────
export async function listJobs(): Promise<JobDescription[]> {
  return request("/api/v1/jobs");
}

export async function uploadJob(
  file?: File,
  text?: string
): Promise<JDUploadResponse> {
  const form = new FormData();
  if (file) form.append("file", file);
  if (text) form.append("text", text);
  return request("/api/v1/jobs/upload", { method: "POST", body: form });
}

export async function getJob(jdId: string): Promise<JobDescription> {
  return request(`/api/v1/jobs/${jdId}`);
}

export async function updateWeights(
  jdId: string,
  weights: Record<string, number>
): Promise<JobDescription> {
  return request(`/api/v1/jobs/${jdId}/weights`, {
    method: "PUT",
    body: JSON.stringify({ weights }),
  });
}

// ── Candidates ───────────────────────────────────────────────
export async function uploadCandidates(
  file?: File,
  text?: string
): Promise<CandidateUploadResponse> {
  const form = new FormData();
  if (file) form.append("file", file);
  if (text) form.append("text", text);
  return request("/api/v1/candidates/upload", { method: "POST", body: form });
}

// ── Matching ─────────────────────────────────────────────────
export async function triggerMatch(jdId: string): Promise<MatchTriggerResponse> {
  return request(`/api/v1/match/${jdId}`, { method: "POST" });
}

export async function getMatchResults(
  jdId: string,
  topK = 50,
  threshold = 0
): Promise<MatchListResponse> {
  return request(`/api/v1/match/${jdId}?top_k=${topK}&threshold=${threshold}`);
}

export async function getMatchDetail(
  jdId: string,
  candidateId: string
): Promise<MatchResult> {
  return request(`/api/v1/match/${jdId}/${candidateId}`);
}

export async function submitFeedback(
  jdId: string,
  candidateId: string,
  feedback: "positive" | "negative"
): Promise<{ message: string }> {
  return request(`/api/v1/match/${jdId}/${candidateId}/feedback`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
  });
}
