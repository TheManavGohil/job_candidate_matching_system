"""
CSV candidate parser — reads CSV, normalizes, and produces candidate dicts.
"""

import io
import logging
from typing import Dict, Any, List

import pandas as pd

from api.utils.synonym_map import normalize_skills

logger = logging.getLogger(__name__)

# Common column name mappings
COLUMN_MAP = {
    "name": ["name", "full_name", "candidate_name", "fullname", "applicant"],
    "email": ["email", "email_address", "e-mail", "mail"],
    "skills": ["skills", "parsed_skills", "technical_skills", "technologies", "tech_stack", "competencies"],
    "years_of_experience": ["years_of_experience", "experience_years", "yoe", "years", "total_experience", "experience"],
    "education": ["education", "degree", "qualification", "academic", "highest_degree"],
    "current_title": ["current_title", "title", "job_title", "position", "role", "designation", "current_role"],
    "work_summary": ["work_summary", "summary", "experience_summary", "work_experience", "description", "about", "bio", "profile"],
    "location": ["location", "city", "country", "address"],
    "notice_period": ["notice_period", "notice", "availability"],
}


def _find_column(df_columns: List[str], candidates: List[str]) -> str | None:
    """Find the first matching column name from a list of candidates."""
    df_cols_lower = {c.lower().strip(): c for c in df_columns}
    for candidate in candidates:
        if candidate.lower() in df_cols_lower:
            return df_cols_lower[candidate.lower()]
    return None


def _parse_skills_value(val) -> List[str]:
    """Parse a skills value that could be a string, list, or comma-separated."""
    if pd.isna(val) or val is None:
        return []
    val = str(val).strip()
    if not val:
        return []
    # Try JSON-like list
    if val.startswith("["):
        import json
        try:
            parsed = json.loads(val.replace("'", '"'))
            if isinstance(parsed, list):
                return [str(s).strip() for s in parsed if str(s).strip()]
        except Exception:
            pass
    # Comma or semicolon separated
    delimiters = [",", ";", "|"]
    for d in delimiters:
        if d in val:
            return [s.strip() for s in val.split(d) if s.strip()]
    return [val]


def _safe_float(val) -> float | None:
    """Safely convert a value to float."""
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        import re
        m = re.search(r"(\d+\.?\d*)", str(val))
        return float(m.group(1)) if m else None


def parse_csv(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Parse a CSV file into a list of candidate dicts.

    Returns:
        List of dicts, each ready for candidate creation.
    """
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {e}")

    if df.empty:
        raise ValueError("CSV file is empty")

    logger.info(f"Parsing CSV with {len(df)} rows and columns: {list(df.columns)}")

    # Map columns
    col_map = {}
    for field, candidates in COLUMN_MAP.items():
        found = _find_column(list(df.columns), candidates)
        if found:
            col_map[field] = found

    candidates = []
    for idx, row in df.iterrows():
        try:
            raw_data = row.to_dict()
            # Clean NaN values from raw_data
            raw_data = {k: (None if pd.isna(v) else v) for k, v in raw_data.items()}

            cand = {
                "name": str(row[col_map["name"]]).strip() if "name" in col_map and pd.notna(row.get(col_map["name"])) else None,
                "email": str(row[col_map["email"]]).strip() if "email" in col_map and pd.notna(row.get(col_map["email"])) else None,
                "skills": [],
                "years_of_experience": None,
                "education": None,
                "current_title": None,
                "work_summary": None,
                "raw_data": raw_data,
            }

            # Skills
            if "skills" in col_map:
                raw_skills = _parse_skills_value(row.get(col_map["skills"]))
                cand["skills"] = normalize_skills(raw_skills)

            # Years of experience
            if "years_of_experience" in col_map:
                cand["years_of_experience"] = _safe_float(row.get(col_map["years_of_experience"]))

            # Education
            if "education" in col_map and pd.notna(row.get(col_map["education"])):
                cand["education"] = str(row[col_map["education"]]).strip()

            # Current title
            if "current_title" in col_map and pd.notna(row.get(col_map["current_title"])):
                cand["current_title"] = str(row[col_map["current_title"]]).strip()

            # Work summary — concatenate available text fields
            summary_parts = []
            if "work_summary" in col_map and pd.notna(row.get(col_map["work_summary"])):
                summary_parts.append(str(row[col_map["work_summary"]]))
            # Also grab any other text-like columns
            for col in df.columns:
                if col not in col_map.values() and pd.notna(row.get(col)):
                    val = str(row[col])
                    if len(val) > 50:  # Likely a text field
                        summary_parts.append(val)
            cand["work_summary"] = "\n".join(summary_parts).strip() or None

            # Store location/notice in raw_data
            if "location" in col_map and pd.notna(row.get(col_map["location"])):
                cand["raw_data"]["location"] = str(row[col_map["location"]])
            if "notice_period" in col_map and pd.notna(row.get(col_map["notice_period"])):
                cand["raw_data"]["notice_period"] = str(row[col_map["notice_period"]])

            candidates.append(cand)
        except Exception as e:
            logger.warning(f"Skipping row {idx}: {e}")
            continue

    logger.info(f"Parsed {len(candidates)} candidates from CSV")
    return candidates
