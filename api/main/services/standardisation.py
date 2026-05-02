"""
LLM-based standardisation – convert raw text + sections into strict JSON schemas.
Uses Groq (llama-3.1-70b-versatile) with structured output and retry logic.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from groq import Groq

from main.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Groq | None = None


def _get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _parse_llm_json(content: str) -> dict:
    """Robustly parse LLM output – strips markdown fences and normalises whitespace."""
    # Strip ```json ... ``` or ``` ... ``` fences
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    # Some models return newlines inside key names – find the JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


# ═══════════════════════════════════════════════════════════════
#  JD Standardisation
# ═══════════════════════════════════════════════════════════════

JD_PROMPT = """You are an expert recruiter parsing a Job Description.
Given the raw text below, extract and return a JSON object with EXACTLY these fields:

{{
  "title": "job title string",
  "company_context": "brief company/team context",
  "required_skills": ["skill1", "skill2", ...],
  "preferred_skills": ["skill1", "skill2", ...],
  "responsibilities": ["resp1", "resp2", ...],
  "qualifications": {{
    "degree": "required degree or empty string",
    "field": "field of study or empty string",
    "min_years": 0
  }},
  "context": "industry/domain summary paragraph",
  "evidence": {{
    "required_skills": "exact quote from text supporting skills",
    "responsibilities": "exact quote from text supporting responsibilities",
    "qualifications": "exact quote from text supporting qualifications"
  }}
}}

Rules:
- Output ONLY valid JSON, no markdown, no extra text.
- If a section is missing, use empty string or empty list.
- For min_years, extract the minimum years of experience mentioned, default 0.
- evidence fields must be direct quotes from the original text.

RAW JOB DESCRIPTION TEXT:
---
{raw_text}
---
"""


def standardise_jd(raw_text: str, sections: dict[str, str] | None = None) -> dict[str, Any]:
    """Standardise a JD into structured JSON using LLM."""
    client = _get_groq_client()
    prompt = JD_PROMPT.format(raw_text=raw_text[:8000])

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = _parse_llm_json(content)
            # Validate required keys
            required_keys = ["title", "required_skills", "responsibilities"]
            if all(k in result for k in required_keys):
                return result
            raise ValueError(f"Missing keys: {set(required_keys) - set(result.keys())}")
        except Exception as e:
            logger.warning(f"JD standardisation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                prompt += f"\n\nPrevious attempt failed with error: {e}. Please fix and try again."
            else:
                logger.error("JD standardisation failed after 2 attempts, returning minimal structure")
                return _minimal_jd(raw_text, sections)

    return _minimal_jd(raw_text, sections)


def _minimal_jd(raw_text: str, sections: dict[str, str] | None = None) -> dict[str, Any]:
    """Fallback minimal JD structure when LLM fails."""
    return {
        "title": "",
        "company_context": "",
        "required_skills": [],
        "preferred_skills": [],
        "responsibilities": [],
        "qualifications": {"degree": "", "field": "", "min_years": 0},
        "context": raw_text[:500] if raw_text else "",
        "evidence": {},
    }


# ═══════════════════════════════════════════════════════════════
#  Candidate Standardisation
# ═══════════════════════════════════════════════════════════════

CANDIDATE_PROMPT = """You are an expert recruiter parsing a candidate resume/profile.
Given the raw text below, extract and return a JSON object with EXACTLY these fields:

{{
  "name": "candidate name",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {{
      "company": "company name",
      "role": "job title",
      "duration": "e.g. Jan 2020 - Dec 2022",
      "description": "what they did"
    }}
  ],
  "education": [
    {{
      "institution": "university name",
      "degree": "degree type",
      "field": "field of study",
      "year": "graduation year"
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": "what the project does",
      "tech": ["tech1", "tech2"]
    }}
  ],
  "total_years": 0.0,
  "summary": "1-2 sentence professional summary"
}}

Rules:
- Output ONLY valid JSON, no markdown, no extra text.
- If a section is missing, use empty string or empty list.
- total_years should be the total years of professional experience (float).
- Extract ALL skills mentioned anywhere in the document.

RAW RESUME/PROFILE TEXT:
---
{raw_text}
---
"""


def standardise_candidate(raw_text: str, sections: dict[str, str] | None = None) -> dict[str, Any]:
    """Standardise a candidate profile into structured JSON using LLM."""
    client = _get_groq_client()
    prompt = CANDIDATE_PROMPT.format(raw_text=raw_text[:8000])

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = _parse_llm_json(content)
            if "skills" in result:
                return result
            raise ValueError("Missing 'skills' key")
        except Exception as e:
            logger.warning(f"Candidate standardisation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                prompt += f"\n\nPrevious attempt failed with error: {e}. Please fix."
            else:
                logger.error("Candidate standardisation failed, returning minimal structure")
                return _minimal_candidate(raw_text, sections)

    return _minimal_candidate(raw_text, sections)


def _minimal_candidate(raw_text: str, sections: dict[str, str] | None = None) -> dict[str, Any]:
    """Fallback minimal candidate structure when LLM fails."""
    return {
        "name": "",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "total_years": 0.0,
        "summary": raw_text[:300] if raw_text else "",
    }
