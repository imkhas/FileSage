from __future__ import annotations

from pathlib import Path


def _next_available_path(dest: Path) -> Path:
    counter = 1
    candidate = dest
    while candidate.exists():
        stem = dest.stem
        suffix = dest.suffix
        candidate = dest.parent / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def resolve_destination(target_dir: str | Path, filename: str) -> Path:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    dest = target / filename
    return _next_available_path(dest)


def handle_existing(dest_path: Path) -> Path:
    if not dest_path.exists():
        return dest_path
    return _next_available_path(dest_path)
