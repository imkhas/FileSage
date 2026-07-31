from __future__ import annotations

import re
from pathlib import Path

_COPY_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")
_VERSION = re.compile(r"[-_\s]+v\.?\d+(?:\.\d+)*\b", re.IGNORECASE)
_TRAILING_NUMBER = re.compile(r"[-_](?!\d{4}\b)\d{1,2}$")
_CLUTTER_WORDS = {
    "final", "finalized", "latest", "new", "newest", "copy", "backup",
    "draft", "edited", "updated", "revised", "old", "temp", "tmp",
}


def _clean(stem: str) -> str:
    cleaned = _COPY_SUFFIX.sub("", stem)
    cleaned = _VERSION.sub("", cleaned)
    cleaned = _TRAILING_NUMBER.sub("", cleaned)

    tokens = re.split(r"[-_\s]+", cleaned)
    seen: set[str] = set()
    kept: list[str] = []
    for token in tokens:
        if not token or token.lower() in _CLUTTER_WORDS:
            continue
        if token.lower() in seen:
            continue
        seen.add(token.lower())
        kept.append(token)

    separator = "_"
    if "_" not in stem and "-" in stem:
        separator = "-"
    return separator.join(kept).strip(" _.-")


def suggest_name(path: str | Path) -> str | None:
    p = Path(path)
    stem = p.stem
    suffix = p.suffix

    cleaned = _clean(stem)
    if suffix and cleaned.endswith(suffix):
        cleaned = cleaned[: -len(suffix)]

    if not cleaned or cleaned.lower() == stem.lower():
        return None
    return cleaned + suffix
