from __future__ import annotations

import tempfile
from pathlib import Path

from organizer.extractor import extract_text


def test_extract_text_plain():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Hello FileSage Text")
        path = Path(f.name)

    try:
        text = extract_text(path)
        assert "Hello FileSage Text" in text
    finally:
        path.unlink(missing_ok=True)


def test_extract_text_unsupported_returns_empty():
    with tempfile.NamedTemporaryFile("w", suffix=".unknown", delete=False) as f:
        f.write("Some content")
        path = Path(f.name)

    try:
        text = extract_text(path)
        assert text == ""
    finally:
        path.unlink(missing_ok=True)


def test_extract_image_returns_string():
    with tempfile.NamedTemporaryFile("w", suffix=".png", delete=False) as f:
        path = Path(f.name)

    try:
        # Calling extract_text on an empty or invalid image should gracefully return "" without crashing
        text = extract_text(path)
        assert isinstance(text, str)
    finally:
        path.unlink(missing_ok=True)
