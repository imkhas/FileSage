from __future__ import annotations

import hashlib
from pathlib import Path

from organizer.extractor import EXTRACTABLE_EXTENSIONS, IMAGE_EXTENSIONS, extract_text

_CHUNK_SIZE = 1 << 20
TEXT_EXTENSIONS = EXTRACTABLE_EXTENSIONS | {".pdf", ".docx"}
_TEXT_SIMILARITY_THRESHOLD = 0.92
_MIN_TEXT_LENGTH = 40
_TEXT_LENGTH_RATIO = 1.4


def content_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def find_exact_duplicates(files: list[Path]) -> list[list[Path]]:
    by_size: dict[int, list[Path]] = {}
    for f in files:
        try:
            size = f.stat().st_size
        except OSError:
            continue
        by_size.setdefault(size, []).append(f)

    groups: list[list[Path]] = []
    for size, group in by_size.items():
        if len(group) < 2 or size == 0:
            continue
        by_hash: dict[str, list[Path]] = {}
        for f in group:
            try:
                by_hash.setdefault(content_hash(f), []).append(f)
            except OSError:
                continue
        for paths in by_hash.values():
            if len(paths) >= 2:
                groups.append(sorted(paths))
    return groups


def dhash(path: str | Path, hash_size: int = 8) -> int | None:
    try:
        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("L").resize((hash_size + 1, hash_size))
            px = list(img.getdata())
    except Exception:
        return None

    value = 0
    for row in range(hash_size):
        for col in range(hash_size):
            left = px[row * (hash_size + 1) + col]
            right = px[row * (hash_size + 1) + col + 1]
            value = (value << 1) | (1 if left > right else 0)
    return value


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def find_image_duplicates(files: list[Path], max_distance: int = 2) -> list[list[Path]]:
    hashed: list[tuple[Path, int]] = []
    for f in files:
        if f.suffix.lower() in IMAGE_EXTENSIONS:
            h = dhash(f)
            if h is not None:
                hashed.append((f, h))

    groups: list[list[Path]] = []
    used: set[Path] = set()
    for i, (f1, h1) in enumerate(hashed):
        if f1 in used:
            continue
        group = [f1]
        for f2, h2 in hashed[i + 1 :]:
            if f2 in used:
                continue
            if _hamming(h1, h2) <= max_distance:
                group.append(f2)
        if len(group) >= 2:
            for p in group:
                used.add(p)
            groups.append(sorted(group))
    return groups


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def text_similarity(a: str, b: str) -> float:
    a, b = _normalize_text(a), _normalize_text(b)
    if not a or not b:
        return 0.0
    from difflib import SequenceMatcher

    return SequenceMatcher(None, a, b).ratio()


def find_text_duplicates(
    files: list[Path],
    threshold: float = _TEXT_SIMILARITY_THRESHOLD,
) -> list[list[Path]]:
    texts: list[tuple[Path, str]] = []
    for f in files:
        if f.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        norm = _normalize_text(extract_text(f))
        if len(norm) >= _MIN_TEXT_LENGTH:
            texts.append((f, norm))
    texts.sort(key=lambda item: len(item[1]))

    groups: list[list[Path]] = []
    used: set[Path] = set()
    for i, (f1, t1) in enumerate(texts):
        if f1 in used:
            continue
        group = [f1]
        for j in range(i + 1, len(texts)):
            f2, t2 = texts[j]
            if f2 in used:
                continue
            if len(t2) > len(t1) * _TEXT_LENGTH_RATIO:
                break
            if text_similarity(t1, t2) >= threshold:
                group.append(f2)
        if len(group) >= 2:
            for p in group:
                used.add(p)
            groups.append(sorted(group))
    return groups


def find_duplicates(files: list[Path]) -> list[list[Path]]:
    groups: list[list[Path]] = []
    groups.extend(find_exact_duplicates(files))
    groups.extend(find_image_duplicates(files))
    groups.extend(find_text_duplicates(files))
    return _merge_groups(groups)


def _merge_groups(groups: list[list[Path]]) -> list[list[Path]]:
    parent: dict[Path, Path] = {}

    def find(p: Path) -> Path:
        parent.setdefault(p, p)
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    def union(a: Path, b: Path) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for group in groups:
        if len(group) >= 2:
            for p in group[1:]:
                union(group[0], p)

    merged: dict[Path, list[Path]] = {}
    for p in parent:
        merged.setdefault(find(p), []).append(p)
    return [sorted(ps) for ps in merged.values() if len(ps) >= 2]
