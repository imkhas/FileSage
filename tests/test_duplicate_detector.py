from __future__ import annotations

import random
import tempfile
from pathlib import Path

from organizer.duplicate_detector import (
    content_hash,
    dhash,
    find_duplicates,
    find_exact_duplicates,
    find_image_duplicates,
    find_text_duplicates,
    text_similarity,
)


def _dir(files: dict[str, str]) -> str:
    d = tempfile.mkdtemp()
    for name, content in files.items():
        p = Path(d) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return d


def _make_png(path: Path, seed: int) -> None:
    from PIL import Image

    random.seed(seed)
    img = Image.new("L", (32, 32))
    for y in range(32):
        for x in range(32):
            img.putpixel((x, y), random.randint(0, 255))
    img.save(path)


def test_content_hash_changes_with_content():
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp) / "a.txt"
        b = Path(tmp) / "b.txt"
        a.write_text("hello", encoding="utf-8")
        b.write_text("world", encoding="utf-8")
        assert content_hash(a) != content_hash(b)
        assert content_hash(a) == content_hash(a)


def test_find_exact_duplicates():
    d = _dir({
        "one.txt": "identical content",
        "two.txt": "identical content",
        "three.txt": "different content",
    })
    files = [Path(d) / n for n in ("one.txt", "two.txt", "three.txt")]
    groups = find_exact_duplicates(files)
    assert len(groups) == 1
    assert sorted(groups[0]) == sorted([Path(d) / "one.txt", Path(d) / "two.txt"])


def test_find_text_duplicates_similar():
    d = _dir({
        "v1.txt": "This is a machine learning report about object detection. " * 3,
        "v2.txt": "This is a machine learning report about object detection. " * 3,
        "unrelated.txt": "Grocery shopping list: milk eggs bread butter cheese. ",
    })
    files = [Path(d) / n for n in ("v1.txt", "v2.txt", "unrelated.txt")]
    groups = find_text_duplicates(files)
    assert len(groups) == 1
    assert sorted(groups[0]) == sorted([Path(d) / "v1.txt", Path(d) / "v2.txt"])


def test_text_similarity_identical_is_one():
    assert text_similarity("hello world", "hello world") == 1.0


def test_find_image_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp) / "a.png"
        b = Path(tmp) / "b.png"
        c = Path(tmp) / "c.png"
        _make_png(a, seed=1)
        _make_png(b, seed=1)
        _make_png(c, seed=2)
        assert dhash(a) == dhash(b)
        groups = find_image_duplicates([a, b, c])
        assert len(groups) == 1
        assert sorted(groups[0]) == sorted([a, b])


def test_find_duplicates_merges_overlap():
    d = _dir({
        "x.txt": "duplicate body " * 5,
        "y.txt": "duplicate body " * 5,
    })
    x, y = Path(d) / "x.txt", Path(d) / "y.txt"
    groups = find_duplicates([x, y])
    assert len(groups) == 1
    assert sorted(groups[0]) == sorted([x, y])
