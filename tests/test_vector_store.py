from __future__ import annotations

import json
import tempfile
from pathlib import Path

import faiss
import numpy as np

from organizer import vector_store
from organizer.database import connect, upsert_file


def _file_row(tmp: Path, name: str, content: str) -> dict:
    return {
        "path": str(tmp / name),
        "name": name,
        "extension": ".txt",
        "size": len(content),
        "modified": 0,
        "category": None,
        "content_text": content,
        "indexed_at": 0,
    }


def _seed_db(tmp: Path) -> None:
    conn = connect(tmp)
    upsert_file(conn, _file_row(tmp, "a.txt", "alpha report"))
    upsert_file(conn, _file_row(tmp, "b.txt", "beta notes"))
    conn.close()


def _embeddings(texts: list[str]) -> np.ndarray:
    arr = np.array(
        [[sum(ord(c) for c in text) + i for i in range(4)] for text in texts],
        dtype=np.float32,
    )
    return arr / np.linalg.norm(arr, axis=1, keepdims=True)


def test_build_index_creates_files(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed_db(root)
        vector_dir = root / "vectors"
        count = vector_store.build_index(db_path=root, vector_dir=vector_dir)
        assert count == 2
        index_dir = vector_dir / vector_store.INDEX_DIR
        assert (index_dir / vector_store.INDEX_FILE).exists()
        assert (index_dir / vector_store.ID_MAP_FILE).exists()


def test_search_index_round_trip(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed_db(root)
        vector_dir = root / "vectors"
        vector_store.build_index(db_path=root, vector_dir=vector_dir)

        query = _embeddings(["alpha report"])
        results = vector_store.search_index(query, limit=5, vector_dir=vector_dir)
        assert len(results) == 2
        assert results[0][1] >= results[1][1]

        query_alpha = _embeddings(["alpha"])
        results_alpha = vector_store.search_index(
            query_alpha, limit=1, vector_dir=vector_dir
        )
        assert len(results_alpha) == 1


def test_build_index_embeds_no_content_file_by_name(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        conn = connect(root)
        upsert_file(conn, _file_row(root, "empty.txt", ""))
        conn.close()
        count = vector_store.build_index(db_path=root, vector_dir=root / "vectors")
        assert count == 1


def test_search_index_missing_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        results = vector_store.search_index(
            np.zeros((1, 4), dtype=np.float32), vector_dir=Path(tmp)
        )
        assert results == []


def test_has_index():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vector_dir = root / "vectors"
        assert not vector_store.has_index(vector_dir=vector_dir)
        _seed_db(root)
        vector_store.build_index(db_path=root, vector_dir=vector_dir)
        assert vector_store.has_index(vector_dir=vector_dir)


def test_build_index_batches_large_set(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        conn = connect(root)
        for i in range(vector_store.BATCH_SIZE + 2):
            upsert_file(conn, _file_row(root, f"f{i}.txt", f"file number {i}"))
        conn.close()
        count = vector_store.build_index(db_path=root, vector_dir=root / "vectors")
        assert count == vector_store.BATCH_SIZE + 2


def test_build_index_resumes_after_partial_run(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vector_dir = root / "vectors"
        conn = connect(root)
        for i in range(4):
            upsert_file(conn, _file_row(root, f"f{i}.txt", f"file number {i}"))
        conn.close()
        vector_store.build_index(db_path=root, vector_dir=vector_dir)

        conn = connect(root)
        upsert_file(conn, _file_row(root, "extra.txt", "extra file"))
        conn.close()

        count = vector_store.build_index(db_path=root, vector_dir=vector_dir)
        assert count == 5
        assert vector_store.has_index(vector_dir=vector_dir)


def test_build_index_repairs_duplicates(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vector_dir = root / "vectors"
        _seed_db(root)
        vector_store.build_index(db_path=root, vector_dir=vector_dir)

        vdir = vector_dir / vector_store.INDEX_DIR
        index_path = vdir / vector_store.INDEX_FILE
        map_path = vdir / vector_store.ID_MAP_FILE

        index = faiss.read_index(str(index_path))
        index.add(index.reconstruct_n(0, index.ntotal))
        faiss.write_index(index, str(index_path))

        id_map = json.loads(map_path.read_text(encoding="utf-8"))
        n = len(id_map)
        for i, fid in enumerate(list(id_map.values())):
            id_map[str(n + i)] = fid
        map_path.write_text(json.dumps(id_map), encoding="utf-8")

        count = vector_store.build_index(db_path=root, vector_dir=vector_dir)
        assert count == 2
        repaired = json.loads(map_path.read_text(encoding="utf-8"))
        assert len(repaired) == 2


def test_embedding_includes_filename(monkeypatch):
    calls: list[str] = []

    def spy(texts: list[str]) -> np.ndarray:
        calls.extend(texts)
        return _embeddings(texts)

    monkeypatch.setattr(vector_store, "embed_texts", spy)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed_db(root)
        vector_store.build_index(db_path=root, vector_dir=root / "vectors")
    assert any(t.startswith("a.txt\n") for t in calls)
    assert any(t.startswith("b.txt\n") for t in calls)


def test_rebuild_when_meta_missing(monkeypatch):
    monkeypatch.setattr(vector_store, "embed_texts", _embeddings)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vector_dir = root / "vectors"
        _seed_db(root)
        count = vector_store.build_index(db_path=root, vector_dir=vector_dir)
        assert count == 2

        vdir = vector_dir / vector_store.INDEX_DIR
        (vdir / vector_store.META_FILE).unlink()

        count = vector_store.build_index(db_path=root, vector_dir=vector_dir)
        assert count == 2
        assert (vdir / vector_store.META_FILE).exists()
