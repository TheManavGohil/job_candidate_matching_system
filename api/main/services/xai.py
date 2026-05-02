"""
Explainable AI – LLM-generated evidence-based match explanations.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from groq import Groq

from main.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


XAI_PROMPT = """You are an expert recruiter. Given a job description and a candidate profile,
evaluate the match. Use the provided per-section similarity scores to ground your assessment.

You must output a JSON object with the following structure,
and nothing else (no markdown, no extra text):

{{
  "overall_grade": "Strong Match" | "Good Fit" | "Potential" | "Not Recommended",
  "strengths": [
    {{
      "point": "string explaining strength",
      "evidence": "exact quote from candidate profile"
    }}
  ],
  "weaknesses": [
    {{
      "point": "string explaining weakness",
      "evidence": "missing or low similarity area reference"
    }}
  ],
  "recommendation": "1-2 sentence summary"
}}

JOB DESCRIPTION:
{jd_summary}

CANDIDATE PROFILE:
{candidate_summary}

PER-SECTION SIMILARITY SCORES:
{section_scores}

Output ONLY valid JSON, no markdown fences.
"""


def generate_explanation(
    jd_json: dict[str, Any],
    candidate_json: dict[str, Any],
    section_scores: dict[str, float],
) -> dict[str, Any]:
    """Generate an XAI explanation for a JD-candidate match."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    # Build summaries
    jd_summary = _format_jd(jd_json)
    candidate_summary = _format_candidate(candidate_json)
    scores_str = json.dumps(section_scores, indent=2)

    prompt = XAI_PROMPT.format(
        jd_summary=jd_summary,
        candidate_summary=candidate_summary,
        section_scores=scores_str,
    )

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate structure
        if "overall_grade" not in result:
            result["overall_grade"] = "Potential"
        if "strengths" not in result:
            result["strengths"] = []
        if "weaknesses" not in result:
            result["weaknesses"] = []
        if "recommendation" not in result:
            result["recommendation"] = ""

        return result

    except Exception as e:
        logger.error(f"XAI explanation generation failed: {e}")
        return {
            "overall_grade": "Potential",
            "strengths": [],
            "weaknesses": [],
            "recommendation": "Unable to generate detailed explanation.",
        }


def _format_jd(jd: dict[str, Any]) -> str:
    """Format JD JSON into a readable summary for the LLM prompt."""
    parts = [f"Title: {jd.get('title', 'N/A')}"]
    if jd.get("required_skills"):
        parts.append(f"Required Skills: {', '.join(jd['required_skills'])}")
    if jd.get("preferred_skills"):
        parts.append(f"Preferred Skills: {', '.join(jd['preferred_skills'])}")
    if jd.get("responsibilities"):
        parts.append(f"Responsibilities: {'; '.join(jd['responsibilities'][:5])}")
    quals = jd.get("qualifications", {})
    if isinstance(quals, dict):
        parts.append(f"Qualifications: {quals.get('degree', '')} in {quals.get('field', '')}, {quals.get('min_years', 0)}+ years")
    if jd.get("context"):
        parts.append(f"Context: {jd['context'][:300]}")
    return "\n".join(parts)


def _format_candidate(cand: dict[str, Any]) -> str:
    """Format candidate JSON into a readable summary for the LLM prompt."""
    parts = [f"Name: {cand.get('name', 'N/A')}"]
    if cand.get("skills"):
        parts.append(f"Skills: {', '.join(cand['skills'][:20])}")
    if cand.get("experience"):
        for exp in cand["experience"][:3]:
            if isinstance(exp, dict):
                parts.append(f"Experience: {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('duration', '')})")
    if cand.get("education"):
        for edu in cand["education"][:2]:
            if isinstance(edu, dict):
                parts.append(f"Education: {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}")
    if cand.get("projects"):
        for proj in cand["projects"][:3]:
            if isinstance(proj, dict):
                parts.append(f"Project: {proj.get('name', '')} - {proj.get('description', '')[:100]}")
    parts.append(f"Total Years: {cand.get('total_years', 0)}")
    if cand.get("summary"):
        parts.append(f"Summary: {cand['summary'][:200]}")
    return "\n".join(parts)
