from __future__ import annotations

from pathlib import Path

from organizer.renamer import suggest_name


def test_strips_version_tokens():
    assert suggest_name(Path("resume_final_latest_v3.pdf")) == "resume.pdf"


def test_strips_copy_suffix():
    assert suggest_name(Path("invoice(1).pdf")) == "invoice.pdf"


def test_strips_copy_word():
    assert suggest_name(Path("notes_copy.txt")) == "notes.txt"


def test_keeps_years():
    assert suggest_name(Path("report_2026.pdf")) is None


def test_clean_name_unchanged():
    assert suggest_name(Path("document.pdf")) is None


def test_strips_trailing_number():
    assert suggest_name(Path("Photo_2.png")) == "Photo.png"


def test_keeps_long_numbers():
    assert suggest_name(Path("invoice_123.pdf")) is None


def test_dedupes_repeated_word():
    assert suggest_name(Path("my_resume_resume.pdf")) == "my_resume.pdf"


def test_double_extension():
    assert suggest_name(Path("notes.pdf.pdf")) == "notes.pdf"
