"""
Document text extraction — PDF and DOCX support.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    import fitz  # PyMuPDF

    text_parts = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Could not parse PDF: {e}")

    return "\n".join(text_parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document
    import io

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise ValueError(f"Could not parse DOCX: {e}")

    return "\n".join(paragraphs).strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Auto-detect file type and extract text.

    Args:
        file_bytes: raw file content
        filename: original filename (used for extension detection)

    Returns:
        Extracted text as a string.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    elif ext in ("txt", "text", "md"):
        return file_bytes.decode("utf-8", errors="replace").strip()
    else:
        # Attempt to decode as text
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            # Might be a PDF without extension
            try:
                return extract_text_from_pdf(file_bytes)
            except Exception:
                raise ValueError(
                    f"Unsupported file type: .{ext}. Please upload PDF, DOCX, or TXT."
                )
