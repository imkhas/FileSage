from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import organizer.gui as gui
from organizer.cli import build_parser


def test_gui_module_imports_headless():
    assert callable(gui.launch)


def test_gui_subcommand():
    args = build_parser().parse_args(["gui"])
    assert args.command == "gui"


def test_status_text_complete():
    status = {"total": 100, "embedded": 100, "remaining": 0, "complete": True}
    text = gui._status_text(status)
    assert "COMPLETE" in text
    assert "100 / 100" in text


def test_status_text_incomplete():
    status = {"total": 100, "embedded": 40, "remaining": 60, "complete": False}
    text = gui._status_text(status)
    assert "INCOMPLETE" in text
    assert "40 / 100" in text
    assert "60 remaining" in text
    assert "Build vectors" in text


def test_format_results_empty():
    assert gui._format_results([]) == ["No results found."]


def test_format_results_lists_scores():
    results = [{"name": "a.pdf", "path": "/p/a.pdf", "score": 0.91}]
    lines = gui._format_results(results)
    assert lines[0].startswith("Found 1 result")
    assert any("a.pdf" in line and "0.91" in line for line in lines)


def test_smart_report_lines_empty():
    report = SimpleNamespace(files=[], duplicates=[])
    lines = gui._smart_report_lines(report)
    assert "No suggestions" in lines[0]


def test_smart_report_lines_categories_and_renames():
    moved = SimpleNamespace(
        category="Images", new_name=None, file=SimpleNamespace(name="pic.png")
    )
    renamed = SimpleNamespace(
        category=None, new_name="report.pdf", file=SimpleNamespace(name="scan.pdf")
    )
    report = SimpleNamespace(files=[moved, renamed], duplicates=[])
    lines = gui._smart_report_lines(report)
    assert any("pic.png" in line and "Images/" in line for line in lines)
    assert any("scan.pdf" in line and "report.pdf" in line for line in lines)


def test_smart_report_lines_duplicates():
    group = [Path("/a.txt"), Path("/b.txt")]
    report = SimpleNamespace(files=[], duplicates=[group])
    lines = gui._smart_report_lines(report)
    assert any("a.txt" in line and "(keep)" in line for line in lines)
    assert any("b.txt" in line and "(duplicate)" in line for line in lines)


def test_gui_log_handler_sink():
    received = []
    gui.GuiLogHandler(sink=received.append).emit(
        SimpleNamespace(getMessage=lambda: "hello")
    )
    assert received == ["hello"]


def test_api_log_store_roundtrip():
    api = gui.FileSageApi()
    api._log("organize", "first")
    api._log("watch", "second", "primary")
    res = api.get_logs(0)
    assert [e[1:] for e in res["entries"]] == [
        ("organize", "first", ""),
        ("watch", "second", "primary"),
    ]
    assert api.get_logs(res["next"])["entries"] == []


def test_api_search_requires_query():
    api = gui.FileSageApi()
    api.search("   ")
    assert "Type a search query" in api.get_logs(0)["entries"][0][2]


def test_api_organize_requires_path():
    api = gui.FileSageApi()
    result = api.organize("", dry_run=True)
    assert "Enter a folder path" in result
