from __future__ import annotations

from pathlib import Path
import tempfile

from organizer.sorter import scan_directory, categorize_file, organize, undo
from organizer.logger import setup_logger

setup_logger("/tmp/sorter_test_logs")

RULES = {"Images": [".jpg", ".png"], "Docs": [".pdf"]}


def _dir(contents: list[str]) -> str:
    d = tempfile.mkdtemp()
    for name in contents:
        p = Path(d) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("")
    return d


def test_scan_directory_returns_files():
    d = _dir(["a.jpg", "b.pdf", "sub/c.png"])
    files = scan_directory(d)
    names = sorted(str(f.relative_to(d)) for f in files)
    assert names == ["a.jpg", "b.pdf", "sub/c.png"]


def test_scan_directory_ignores_hidden():
    d = _dir(["a.jpg", ".hidden.txt", "sub/.secret/doc.pdf"])
    files = scan_directory(d)
    names = sorted(str(f.relative_to(d)) for f in files)
    assert names == ["a.jpg"]


def test_categorize_file_matches_correct_category():
    assert categorize_file(Path("x.jpg"), RULES) == "Images"
    assert categorize_file(Path("x.png"), RULES) == "Images"
    assert categorize_file(Path("x.pdf"), RULES) == "Docs"


def test_categorize_file_returns_none_for_unknown():
    assert categorize_file(Path("x.mp3"), RULES) is None


def test_organize_dry_run_does_not_move():
    d = _dir(["a.jpg", "b.pdf"])
    results = organize(d, RULES, dry_run=True)
    assert all(r["status"] == "moved" for r in results)
    assert (Path(d) / "a.jpg").exists()


def test_undo_restores_files():
    d = _dir(["a.jpg", "b.pdf"])
    root = Path(d)
    organize(d, RULES)
    assert not (root / "a.jpg").exists()
    assert (root / "Images" / "a.jpg").exists()

    undo_log = list(root.glob(".undo_*.jsonl"))
    assert len(undo_log) == 1
    count = undo(undo_log[0])
    assert count == 2
    assert (root / "a.jpg").exists()
    assert (root / "b.pdf").exists()
