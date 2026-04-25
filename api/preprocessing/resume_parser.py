"""
Resume parser — extracts candidate profile from resume text using
spaCy NER, regex patterns, and skill vocabulary matching.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from api.utils.synonym_map import normalize_skills, extract_skills_from_text

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"[\+]?[\d\s\-\(\)]{7,15}")
DATE_RANGE_RE = re.compile(
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|"
    r"\d{1,2}/\d{4}|\d{4})\s*[-–—to]+\s*"
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|"
    r"\d{1,2}/\d{4}|\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow)",
    re.IGNORECASE,
)
YEARS_EXP_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)", re.IGNORECASE)

DEGREE_LEVELS = {
    "phd": 4, "ph.d": 4, "doctorate": 4, "doctor": 4,
    "master": 3, "m.s.": 3, "m.sc": 3, "mba": 3, "m.tech": 3, "m.e.": 3,
    "bachelor": 2, "b.s.": 2, "b.sc": 2, "b.tech": 2, "b.e.": 2, "bca": 2, "bba": 2,
    "associate": 1, "diploma": 1,
}

SECTION_HEADERS = {
    "experience": re.compile(r"(?:experience|work history|employment|professional experience|career)", re.I),
    "education": re.compile(r"(?:education|academic|qualification|degree)", re.I),
    "skills": re.compile(r"(?:skills|technical skills|technologies|competencies|expertise)", re.I),
    "summary": re.compile(r"(?:summary|objective|profile|about me|overview)", re.I),
    "projects": re.compile(r"(?:projects|portfolio|work samples)", re.I),
    "certifications": re.compile(r"(?:certifications?|licenses?|credentials?)", re.I),
}


def _extract_name_spacy(text: str) -> Optional[str]:
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:1000])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                if 2 <= len(name.split()) <= 4:
                    return name
    except Exception:
        pass
    # Fallback: first line that looks like a name
    for line in text.split("\n")[:5]:
        line = line.strip()
        if line and 2 <= len(line.split()) <= 4 and not EMAIL_RE.search(line):
            if not any(c.isdigit() for c in line) and len(line) < 50:
                return line
    return None


def _extract_email(text: str) -> Optional[str]:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def _split_sections(text: str) -> Dict[str, str]:
    lines = text.split("\n")
    sections = {"full": text}
    current = "header"
    buf = {"header": []}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            buf.setdefault(current, []).append("")
            continue
        matched = False
        for name, pat in SECTION_HEADERS.items():
            if pat.search(stripped) and len(stripped) < 60:
                current = name
                buf.setdefault(name, [])
                matched = True
                break
        if not matched:
            buf.setdefault(current, []).append(stripped)

    for name, lines_list in buf.items():
        sections[name] = "\n".join(lines_list).strip()
    return sections


def _estimate_years(text: str) -> Optional[float]:
    # Try explicit mention first
    m = YEARS_EXP_RE.search(text)
    if m:
        return float(m.group(1))
    # Try date ranges
    matches = DATE_RANGE_RE.findall(text)
    if not matches:
        return None
    total_months = 0
    for match_str in matches:
        try:
            parts = re.split(r'\s*[-–—to]+\s*', match_str, maxsplit=1)
            if len(parts) != 2:
                continue
            start_str, end_str = parts
            start_date = _parse_date(start_str.strip())
            end_date = _parse_date(end_str.strip())
            if start_date and end_date:
                diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                if 0 < diff < 360:
                    total_months += diff
        except Exception:
            continue
    if total_months > 0:
        return round(total_months / 12, 1)
    return None


def _parse_date(s: str) -> Optional[datetime]:
    s = s.strip().lower()
    if s in ("present", "current", "now"):
        return datetime.now()
    formats = ["%B %Y", "%b %Y", "%b. %Y", "%m/%Y", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Try extracting just the year
    m = re.search(r"(\d{4})", s)
    if m:
        return datetime(int(m.group(1)), 1, 1)
    return None


def _extract_degree(text: str) -> Optional[str]:
    text_lower = text.lower()
    best_level = 0
    best_degree = None
    for keyword, level in DEGREE_LEVELS.items():
        if keyword in text_lower and level > best_level:
            best_level = level
            best_degree = keyword.title()
    if best_degree:
        return {1: "Associate/Diploma", 2: "Bachelor", 3: "Master", 4: "PhD"}.get(best_level, best_degree)
    return None


def _extract_current_title(text: str, sections: Dict[str, str]) -> Optional[str]:
    exp_text = sections.get("experience", "")
    if not exp_text:
        exp_text = text
    # Common pattern: title at company, or title - company
    title_patterns = [
        re.compile(r"^(.{5,60})\s+(?:at|@|-|–)\s+", re.MULTILINE),
        re.compile(r"^((?:Senior |Junior |Lead |Staff |Principal )?(?:Software|Data|ML|AI|Backend|Frontend|Full[ -]?Stack|DevOps|Cloud|Platform|Mobile|QA|Security)[\s\w]*(?:Engineer|Developer|Scientist|Analyst|Architect|Manager))", re.MULTILINE | re.IGNORECASE),
    ]
    for pat in title_patterns:
        m = pat.search(exp_text)
        if m:
            title = m.group(1).strip()
            if len(title) < 80:
                return title
    return None


def parse_resume(text: str) -> Dict[str, Any]:
    """Parse resume text into a structured candidate profile."""
    if not text or not text.strip():
        raise ValueError("Resume text is empty")

    text = text.strip()
    sections = _split_sections(text)
    confidence = 1.0

    name = _extract_name_spacy(text)
    email = _extract_email(text)
    skills = extract_skills_from_text(text)
    skills = normalize_skills(skills)
    years = _estimate_years(text)
    edu_section = sections.get("education", text)
    education = _extract_degree(edu_section)
    current_title = _extract_current_title(text, sections)
    work_summary = sections.get("experience", "")
    if not work_summary:
        work_summary = sections.get("summary", text[:2000])

    if not name:
        confidence -= 0.2
    if not skills:
        confidence -= 0.3
    if not years:
        confidence -= 0.1

    return {
        "name": name, "email": email,
        "skills": skills,
        "years_of_experience": years,
        "education": education,
        "current_title": current_title,
        "work_summary": work_summary,
        "raw_text": text,
        "confidence": max(0.1, confidence),
    }
