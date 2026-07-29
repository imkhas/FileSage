from __future__ import annotations

import json
import time
from pathlib import Path

from organizer.duplicate_handler import resolve_destination
from organizer.logger import get_logger
from organizer.utils import ensure_directory, get_file_extension, is_locked, safe_move


def scan_directory(path: str | Path, recursive: bool = False) -> list[Path]:
    root = Path(path)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    files: list[Path] = []
    log = get_logger()
    entries = root.rglob("*") if recursive else root.glob("*")
    for entry in entries:
        try:
            if entry.is_file() and not _is_hidden(entry):
                files.append(entry)
        except OSError as e:
            log.warning("Skipping file due to OS permission/security restriction (%s): %s", entry.name, e)
    return files


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(path.anchor).parts)


def categorize_file(file: Path, rules: dict[str, list[str]]) -> str | None:
    ext = get_file_extension(file)
    for category, extensions in rules.items():
        if ext in extensions:
            return category
    return None


def organize(
    path: str | Path,
    config: dict[str, list[str]],
    dry_run: bool = False,
    recursive: bool = False,
) -> list[dict]:
    log = get_logger()
    root = Path(path)
    results: list[dict] = []
    undo_log: list[dict] = []
    undo_path = root / f".undo_{int(time.time())}.jsonl"

    for file in scan_directory(root, recursive=recursive):
        category = categorize_file(file, config)

        if category is None:
            results.append({
                "file": str(file),
                "category": None,
                "status": "skipped",
                "detail": "No matching category",
            })
            continue

        if is_locked(file):
            results.append({
                "file": str(file),
                "category": category,
                "status": "skipped",
                "detail": "File is locked or in use",
            })
            continue

        rel_path = file.relative_to(root)
        category_dir = ensure_directory(root / category)

        try:
            dest = resolve_destination(category_dir, rel_path.name)
        except Exception as e:
            results.append({
                "file": str(file),
                "category": category,
                "status": "error",
                "detail": str(e),
            })
            continue

        if dry_run:
            results.append({
                "file": str(file),
                "category": category,
                "status": "moved",
                "detail": f"Would move to {dest}",
            })
            continue

        try:
            safe_move(file, dest)
            undo_log.append({"src": str(dest), "dst": str(file)})
            log.info("Moved %s -> %s", file.name, category)
            results.append({
                "file": str(file),
                "category": category,
                "status": "moved",
                "detail": str(dest),
            })
        except Exception as e:
            log.error("Failed to move %s: %s", file.name, e)
            results.append({
                "file": str(file),
                "category": category,
                "status": "error",
                "detail": str(e),
            })

    if undo_log and not dry_run:
        undo_path.write_text(
            "\n".join(json.dumps(entry) for entry in undo_log),
            encoding="utf-8",
        )
        log.info("Undo log written to %s", undo_path)

    return results


def undo(undo_log_path: str | Path) -> int:
    log = get_logger()
    path = Path(undo_log_path)

    if path.is_dir():
        logs = sorted(path.glob(".undo_*.jsonl"))
        if not logs:
            log.error("No undo log files found in directory: %s", path)
            return 0
        path = logs[-1]  # Pick the latest undo log file
        log.info("Using latest undo log: %s", path.name)

    if not path.exists():
        log.error("Undo log not found: %s", path)
        return 0

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    restored = 0

    for line in lines:
        if not line.strip():
            continue
        entry = json.loads(line)
        src, dst = Path(entry["src"]), Path(entry["dst"])
        if not src.exists():
            log.warning("Source not found, skipping: %s", src)
            continue
        try:
            safe_move(src, dst)
            log.info("Restored %s -> %s", src.name, dst)
            restored += 1
        except Exception as e:
            log.error("Failed to restore %s: %s", src, e)

    log.info("Undo complete: %d files restored", restored)
    return restored
