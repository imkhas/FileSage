from __future__ import annotations

import tempfile
from pathlib import Path

from organizer.duplicate_handler import resolve_destination, handle_existing


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def test_resolve_destination_no_conflict():
    with tempfile.TemporaryDirectory() as tmp:
        result = resolve_destination(tmp, "new.txt")
        assert result == Path(tmp) / "new.txt"


def test_resolve_destination_appends_suffix():
    with tempfile.TemporaryDirectory() as tmp:
        _touch(Path(tmp) / "doc.pdf")
        result = resolve_destination(tmp, "doc.pdf")
        assert result.name == "doc_1.pdf"


def test_resolve_destination_multiple_suffixes():
    with tempfile.TemporaryDirectory() as tmp:
        _touch(Path(tmp) / "doc.txt")
        r1 = resolve_destination(tmp, "doc.txt")
        assert r1.name == "doc_1.txt"
        _touch(r1)
        r2 = resolve_destination(tmp, "doc.txt")
        assert r2.name == "doc_2.txt"
        _touch(r2)
        r3 = resolve_destination(tmp, "doc.txt")
        assert r3.name == "doc_3.txt"


def test_handle_existing_returns_available_path():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "test.txt"
        assert handle_existing(p) == p
        _touch(p)
        result = handle_existing(p)
        assert result.name == "test_1.txt"
        _touch(result)
        result2 = handle_existing(p)
        assert result2.name == "test_2.txt"
