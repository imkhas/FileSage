from __future__ import annotations

import tempfile
from pathlib import Path

from organizer.smart import (
    SmartReport,
    analyze,
    apply_actions,
    print_report,
    suggest_category,
)

RULES = {"Documents": [".pdf", ".txt"], "Images": [".png", ".jpg"]}


def _dir(files: dict[str, str]) -> str:
    d = tempfile.mkdtemp()
    for name, content in files.items():
        p = Path(d) / name
        p.write_text(content, encoding="utf-8")
    return d


def test_suggest_category_content_based():
    d = _dir({"invoice123.pdf": "payment due invoice amount total"})
    assert suggest_category(Path(d) / "invoice123.pdf", RULES) == "Finance"


def test_suggest_category_from_underscored_filename():
    d = _dir({"invoice_2026.pdf": "statement"})
    assert suggest_category(Path(d) / "invoice_2026.pdf", RULES) == "Finance"


def test_suggest_category_from_filename():
    d = _dir({"resume_2026.pdf": "personal details and skills"})
    assert suggest_category(Path(d) / "resume_2026.pdf", RULES) == "Career"


def test_suggest_category_falls_back_to_extension():
    d = _dir({"photo.png": ""})
    assert suggest_category(Path(d) / "photo.png", RULES) == "Images"


def test_analyze_builds_report():
    d = _dir({
        "invoice_123.pdf": "invoice total payment",
        "resume_final_v3.pdf": "my resume",
    })
    report = analyze(d, RULES)
    categories = {fs.file.name: fs.category for fs in report.files}
    assert categories.get("invoice_123.pdf") == "Finance"
    assert categories.get("resume_final_v3.pdf") == "Career"

    renames = {fs.file.name: fs.new_name for fs in report.files}
    assert renames.get("resume_final_v3.pdf") == "resume.pdf"


def test_apply_actions_moves_and_renames():
    d = _dir({"invoice_123.pdf": "invoice total payment due"})
    report = analyze(d, RULES)
    root = Path(d)
    results = apply_actions(root, report)
    assert any(r["action"] == "move" and r["status"] == "applied" for r in results)
    assert (root / "Finance" / "invoice_123.pdf").exists()
    assert not (root / "invoice_123.pdf").exists()


def test_apply_actions_dry_run_no_changes():
    d = _dir({"invoice_123.pdf": "invoice total payment due"})
    report = analyze(d, RULES)
    root = Path(d)
    results = apply_actions(root, report, dry_run=True)
    assert all(r["status"] == "pending" for r in results)
    assert (root / "invoice_123.pdf").exists()
    assert not (root / "Finance").exists()


def test_apply_actions_moves_duplicates():
    d = _dir({
        "same.dat": "identical binary body " * 5,
        "same_copy.dat": "identical binary body " * 5,
    })
    report = analyze(d, RULES)
    root = Path(d)
    assert len(report.duplicates) == 1
    results = apply_actions(root, report)
    assert any(r["action"] == "duplicate" and r["status"] == "applied" for r in results)
    assert (root / "Duplicates" / "same_copy.dat").exists()
    assert (root / "same.dat").exists()


def test_print_report_empty(capsys):
    print_report(SmartReport())
    captured = capsys.readouterr().out
    assert "No suggestions" in captured
