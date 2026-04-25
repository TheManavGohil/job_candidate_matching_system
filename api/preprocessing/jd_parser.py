"""
Job Description parser — extracts structured fields from raw JD text.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from api.utils.synonym_map import normalize_skills, extract_skills_from_text

logger = logging.getLogger(__name__)

YEARS_PATTERNS = [
    re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?", re.IGNORECASE),
    re.compile(r"minimum\s*(?:of)?\s*(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
    re.compile(r"at\s*least\s*(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
]

ROLE_TYPE_MAP = {
    "ai": "AI Engineer", "machine learning": "ML Engineer", "ml": "ML Engineer",
    "data scientist": "Data Scientist", "data engineer": "Data Engineer",
    "backend": "Backend Engineer", "frontend": "Frontend Engineer",
    "full stack": "Full Stack Engineer", "fullstack": "Full Stack Engineer",
    "devops": "DevOps Engineer", "cloud": "Cloud Engineer",
    "mobile": "Mobile Developer", "software engineer": "Software Engineer",
    "nlp": "NLP Engineer", "platform": "Platform Engineer",
    "web developer": "Web Developer", "qa": "QA Engineer",
}

SECTION_PATTERNS = {
    "requirements": re.compile(
        r"(?:requirements|qualifications|must have|required skills|what we.?re looking for)", re.IGNORECASE
    ),
    "preferred": re.compile(
        r"(?:preferred|nice to have|bonus|desired|good to have|plus)", re.IGNORECASE
    ),
    "responsibilities": re.compile(
        r"(?:responsibilities|what you.?ll do|duties|about the role)", re.IGNORECASE
    ),
}


def _split_into_sections(text: str) -> Dict[str, str]:
    lines = text.split("\n")
    sections = {"full": text}
    current = "preamble"
    buf = {"preamble": []}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            buf.setdefault(current, []).append("")
            continue
        matched = False
        for name, pat in SECTION_PATTERNS.items():
            if pat.search(stripped) and len(stripped) < 100:
                current = name
                buf.setdefault(name, [])
                matched = True
                break
        if not matched:
            buf.setdefault(current, []).append(stripped)

    for name, lines_list in buf.items():
        sections[name] = "\n".join(lines_list).strip()
    return sections


def _extract_title(text: str) -> Optional[str]:
    m = re.search(r"(?:job\s*title|position|role)\s*[:]\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) < 120 and not line.startswith("http"):
            return line
    return None


def _extract_years(text: str) -> Optional[float]:
    for pat in YEARS_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                return float(m.group(1))
            except (ValueError, IndexError):
                continue
    return None


def _determine_role_type(title: Optional[str], text: str) -> Optional[str]:
    search = f"{title or ''} {text[:500]}".lower()
    for kw, role in sorted(ROLE_TYPE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if kw in search:
            return role
    return None


def _classify_skills(text: str, sections: Dict[str, str]):
    required, preferred = set(), set()
    if "requirements" in sections and sections["requirements"]:
        required.update(extract_skills_from_text(sections["requirements"]))
    if "preferred" in sections and sections["preferred"]:
        preferred.update(extract_skills_from_text(sections["preferred"]))
    all_skills = extract_skills_from_text(text)
    for s in all_skills:
        if s not in required and s not in preferred:
            preferred.add(s)
    if not required and all_skills:
        required = set(all_skills)
        preferred = set()
    return normalize_skills(list(required)), normalize_skills(list(preferred))


def parse_jd(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("Job description text is empty")
    text = text.strip()
    sections = _split_into_sections(text)
    title = _extract_title(text)
    min_years = _extract_years(text)
    role_type = _determine_role_type(title, text)
    required_skills, preferred_skills = _classify_skills(text, sections)

    parts = []
    for s in ["requirements", "responsibilities"]:
        if s in sections and sections[s]:
            parts.append(sections[s])
    core_req = "\n\n".join(parts) if parts else text[:2000]

    return {
        "title": title, "raw_text": text,
        "required_skills": required_skills, "preferred_skills": preferred_skills,
        "min_years": min_years, "role_type": role_type,
        "core_requirements_text": core_req,
    }
