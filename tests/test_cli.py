from __future__ import annotations

from organizer.cli import build_parser


def _parse(argv: list[str]):
    return build_parser().parse_args(argv)


def test_organize_subcommand():
    args = _parse(["organize", "/some/path"])
    assert args.command == "organize"
    assert args.path == "/some/path"
    assert args.dry_run is False


def test_watch_subcommand():
    args = _parse(["watch", "/some/path"])
    assert args.command == "watch"
    assert args.path == "/some/path"


def test_undo_flag():
    args = _parse(["--undo", "/some/path"])
    assert args.undo == "/some/path"


def test_dry_run_flag():
    args = _parse(["organize", "/some/path", "--dry-run"])
    assert args.dry_run is True


def test_missing_path_errors():
    args = _parse([])
    assert args.command is None
    assert args.undo is None


def test_smart_subcommand():
    args = _parse(["smart", "/some/path", "--dry-run"])
    assert args.command == "smart"
    assert args.path == "/some/path"
    assert args.dry_run is True
    assert args.recursive is False


def test_smart_yes_flag():
    args = _parse(["smart", "/some/path", "-y"])
    assert args.command == "smart"
    assert args.yes is True
