"""
Document parsing – LlamaParse (PDF), python-docx (DOCX), pdfplumber fallback.
Includes spaCy-based section splitting and NER.
"""

from __future__ import annotations

import io
import logging
import re
from typing import Any

import pdfplumber
from docx import Document as DocxDocument

from main.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Heading patterns for section splitting ────────────────────
SECTION_HEADINGS = [
    r"(?i)\b(skills|technical\s+skills|core\s+competencies|technologies)\b",
    r"(?i)\b(experience|work\s+experience|professional\s+experience|employment)\b",
    r"(?i)\b(education|academic|qualifications|certifications)\b",
    r"(?i)\b(projects|personal\s+projects|key\s+projects)\b",
    r"(?i)\b(summary|objective|profile|about)\b",
    r"(?i)\b(responsibilities|duties|key\s+responsibilities)\b",
    r"(?i)\b(requirements|required|must\s+have|minimum\s+qualifications)\b",
    r"(?i)\b(preferred|nice\s+to\s+have|bonus|desired)\b",
]


# ═══════════════════════════════════════════════════════════════
#  Text extraction
# ═══════════════════════════════════════════════════════════════

def parse_pdf_llamaparse(file_bytes: bytes) -> str:
    """Parse PDF using LlamaParse cloud API."""
    try:
        from llama_cloud.client import LlamaCloud

        client = LlamaCloud(token=settings.LLAMA_CLOUD_API_KEY)
        # Use the parsing API
        job = client.parsing.upload_file(
            file=("document.pdf", file_bytes, "application/pdf"),
            parsing_instruction="Extract all text preserving section headings and bullet points.",
        )
        # Wait for result
        result = client.parsing.get_result(job_id=job.id, result_type="markdown")
        return result.markdown if hasattr(result, "markdown") else str(result)
    except Exception as e:
        logger.warning(f"LlamaParse failed, falling back to pdfplumber: {e}")
        return parse_pdf_fallback(file_bytes)


def parse_pdf_fallback(file_bytes: bytes) -> str:
    """Fallback PDF parser using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_text(file_bytes: bytes) -> str:
    """Plain text – just decode."""
    return file_bytes.decode("utf-8", errors="replace")


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Dispatch to the right parser based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
    if ext == "pdf":
        if settings.LLAMA_CLOUD_API_KEY:
            return parse_pdf_llamaparse(file_bytes)
        return parse_pdf_fallback(file_bytes)
    elif ext in ("docx", "doc"):
        return parse_docx(file_bytes)
    else:
        return parse_text(file_bytes)


# ═══════════════════════════════════════════════════════════════
#  Section splitting
# ═══════════════════════════════════════════════════════════════

def split_sections(raw_text: str) -> dict[str, str]:
    """
    Split document text into named sections based on heading detection.
    Returns a dict mapping section_name -> section_text.
    """
    lines = raw_text.split("\n")
    sections: dict[str, list[str]] = {}
    current_section = "summary"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_section in sections:
                sections[current_section].append("")
            continue

        # Check if this line is a heading
        matched_section = _match_heading(stripped)
        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(stripped)

    # Clean up: join lines and strip empty sections
    result = {}
    for name, lines_list in sections.items():
        text = "\n".join(lines_list).strip()
        if text:
            result[name] = text

    return result


def _match_heading(line: str) -> str | None:
    """Check if a line matches a known section heading."""
    # Remove common heading markers
    cleaned = re.sub(r"^[#*\-=•]+\s*", "", line).strip()
    if len(cleaned) > 60:  # Too long to be a heading
        return None

    mapping = {
        "skills": "skills",
        "technical_skills": "skills",
        "core_competencies": "skills",
        "technologies": "skills",
        "experience": "experience",
        "work_experience": "experience",
        "professional_experience": "experience",
        "employment": "experience",
        "education": "education",
        "academic": "education",
        "qualifications": "qualifications",
        "certifications": "education",
        "projects": "projects",
        "personal_projects": "projects",
        "key_projects": "projects",
        "summary": "summary",
        "objective": "summary",
        "profile": "summary",
        "about": "summary",
        "responsibilities": "responsibilities",
        "duties": "responsibilities",
        "key_responsibilities": "responsibilities",
        "requirements": "required_skills",
        "required": "required_skills",
        "must_have": "required_skills",
        "minimum_qualifications": "required_skills",
        "preferred": "preferred_skills",
        "nice_to_have": "preferred_skills",
        "bonus": "preferred_skills",
        "desired": "preferred_skills",
    }

    cleaned_lower = re.sub(r"[^a-z\s]", "", cleaned.lower()).strip()
    cleaned_key = cleaned_lower.replace(" ", "_")

    for pattern, section in mapping.items():
        if pattern in cleaned_key or cleaned_key in pattern:
            return section

    return None


# ═══════════════════════════════════════════════════════════════
#  NER – extract PII for dedup (name, email, phone)
# ═══════════════════════════════════════════════════════════════

def extract_entities(raw_text: str) -> dict[str, str | None]:
    """Extract name, email, phone from text using regex (lightweight NER)."""
    entities: dict[str, str | None] = {"name": None, "email": None, "phone": None}

    # Email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw_text)
    if email_match:
        entities["email"] = email_match.group()

    # Phone
    phone_match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text
    )
    if phone_match:
        entities["phone"] = phone_match.group()

    # Name: try spaCy if available, else take first non-empty line
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(raw_text[:500])  # Only scan the top
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["name"] = ent.text
                break
    except Exception:
        # Fallback: first line that looks like a name
        for line in raw_text.split("\n")[:5]:
            stripped = line.strip()
            if stripped and len(stripped.split()) <= 4 and not re.search(r"[@\d]", stripped):
                entities["name"] = stripped
                break

    return entities
