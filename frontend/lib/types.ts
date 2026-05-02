/**
 * TypeScript types mirroring backend Pydantic schemas.
 */

export interface Company {
  id: string;
  name: string;
  api_key: string;
  created_at: string;
}

export interface JDStandardised {
  title: string;
  company_context: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  qualifications: {
    degree: string;
    field: string;
    min_years: number;
  };
  context: string;
  evidence: Record<string, string>;
}

export interface WeightsMap {
  required_skills: number;
  preferred_skills: number;
  responsibilities: number;
  qualifications: number;
  context: number;
  [key: string]: number;
}

export interface JobDescription {
  jd_id: string;
  company_id: string;
  raw_text: string | null;
  standardised_json: JDStandardised;
  weights: WeightsMap;
  created_at: string;
}

export interface JDUploadResponse {
  jd_id: string;
  task_id: string | null;
  standardised_json: JDStandardised | null;
}

export interface ExperienceEntry {
  company: string;
  role: string;
  duration: string;
  description: string;
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field: string;
  year: string;
}

export interface ProjectEntry {
  name: string;
  description: string;
  tech: string[];
}

export interface CandidateStandardised {
  name: string;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  total_years: number;
  summary: string;
}

export interface CandidateResponse {
  candidate_id: string;
  company_id: string;
  standardised_json: CandidateStandardised;
  created_at: string;
}

export interface CandidateUploadResponse {
  candidate_ids: string[];
  task_ids: string[];
}

export interface StrengthWeakness {
  point: string;
  evidence: string;
}

export interface XAIExplanation {
  overall_grade: "Strong Match" | "Good Fit" | "Potential" | "Not Recommended";
  strengths: StrengthWeakness[];
  weaknesses: StrengthWeakness[];
  recommendation: string;
}

export interface MatchResult {
  id: string;
  candidate_id: string;
  total_score: number;
  section_scores: Record<string, number>;
  xai_explanation: XAIExplanation | null;
  candidate_name: string | null;
  candidate_summary: string | null;
  recruiter_feedback: string | null;
}

export interface MatchListResponse {
  jd_id: string;
  total: number;
  results: MatchResult[];
}

export interface MatchTriggerResponse {
  task_id: string;
  jd_id: string;
  message: string;
}
