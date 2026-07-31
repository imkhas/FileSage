from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from organizer import embedder, vector_store
from organizer.database import connect, upsert_file


def _seed_db(tmp: Path) -> None:
    conn = connect(tmp)
    for name, content in [
        ("alpha.txt", "alpha internship report"),
        ("beta.txt", "beta meeting notes"),
    ]:
        upsert_file(conn, {
            "path": str(tmp / name),
            "name": name,
            "extension": ".txt",
            "size": len(content),
            "modified": 0,
            "category": None,
            "content_text": content,
            "indexed_at": 0,
        })
    conn.close()


def _embeddings(texts: list[str]) -> np.ndarray:
    return np.array(
        [
            [1.0, 0.0, 0.0] if "alpha" in text else [0.0, 1.0, 0.0]
            for text in texts
        ],
        dtype=np.float32,
    )


def test_search_returns_ranked_results(monkeypatch):
    from organizer import search as search_module

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed_db(root)

        monkeypatch.setattr(embedder, "embed_texts", _embeddings)
        monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
        monkeypatch.setattr(
            vector_store, "get_vector_dir", lambda base_dir=None: root / "vectors"
        )

        vector_store.build_index(db_path=root, vector_dir=root / "vectors")

        results = search_module.search("alpha", db_path=root)
        assert len(results) == 2
        assert "score" in results[0]
        assert results[0]["score"] >= results[1]["score"]
        assert "alpha" in results[0]["content_text"]


def test_search_limit_respected(monkeypatch):
    from organizer import search as search_module

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed_db(root)

        monkeypatch.setattr(embedder, "embed_texts", _embeddings)
        monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
        monkeypatch.setattr(
            vector_store, "get_vector_dir", lambda base_dir=None: root / "vectors"
        )

        vector_store.build_index(db_path=root, vector_dir=root / "vectors")

        results = search_module.search("alpha", limit=1, db_path=root)
        assert len(results) == 1


def test_search_no_index_returns_empty(monkeypatch):
    from organizer import search as search_module

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        monkeypatch.setattr(embedder, "embed_texts", _embeddings)
        monkeypatch.setattr(
            vector_store, "get_vector_dir", lambda base_dir=None: root / "vectors"
        )
        assert search_module.search("anything", db_path=root) == []
