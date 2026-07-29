from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


def get_file_extension(path: str | Path) -> str:
    return Path(path).suffix.lower()


def ensure_directory(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_move(src: str | Path, dst: str | Path) -> Path:
    src_path = Path(src)
    dst_path = Path(dst)
    if dst_path.exists():
        raise FileExistsError(f"Destination already exists: {dst_path}")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_path), str(dst_path))
    return dst_path


def is_locked(path: str | Path) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        st = p.stat()
        return not (st.st_mode & stat.S_IWUSR)
    except OSError:
        return True


def generate_summary(results: list[dict]) -> str:
    moved = sum(1 for r in results if r.get("status") == "moved")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    errors = sum(1 for r in results if r.get("status") == "error")
    parts = [f"Moved: {moved}"]
    if skipped:
        parts.append(f"Skipped: {skipped}")
    if errors:
        parts.append(f"Errors: {errors}")
    return f"{', '.join(parts)} ({len(results)} total)"
