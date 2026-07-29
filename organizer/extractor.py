from __future__ import annotations

from pathlib import Path

import fitz
from docx import Document


EXTRACTABLE_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
    ".xml", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".sh", ".bat",
    ".csv", ".log", ".sql", ".java", ".c", ".cpp", ".h", ".rs", ".go",
}

MAX_TEXT_LENGTH = 50_000


def extract_text(path: str | Path) -> str:
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(path)
    if ext == ".docx":
        return _extract_docx(path)
    if ext in EXTRACTABLE_EXTENSIONS:
        return _extract_plain(path)
    return ""


def _extract_pdf(path: Path) -> str:
    try:
        doc = fitz.open(str(path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text[:MAX_TEXT_LENGTH].strip()
    except Exception:
        return ""


def _extract_docx(path: Path) -> str:
    try:
        doc = Document(str(path))
        text = "\n".join(para.text for para in doc.paragraphs)
        return text[:MAX_TEXT_LENGTH].strip()
    except Exception:
        return ""


def _extract_plain(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text[:MAX_TEXT_LENGTH].strip()
    except Exception:
        return ""
