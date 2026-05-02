"""
Utility helpers – hashing, file detection, text cleaning.
"""

from __future__ import annotations

import hashlib
import re


def sha256_hash(text: str) -> str:
    """SHA-256 hash for deduplication (e.g., email addresses)."""
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()


def detect_file_type(filename: str) -> str:
    """Return normalised extension: 'pdf', 'docx', 'csv', 'txt'."""
    if not filename:
        return "txt"
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext in ("pdf",):
        return "pdf"
    elif ext in ("docx", "doc"):
        return "docx"
    elif ext in ("csv",):
        return "csv"
    return "txt"


def clean_text(text: str) -> str:
    """Normalise whitespace, strip control chars."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def truncate(text: str, max_len: int = 2000) -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
