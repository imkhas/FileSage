from __future__ import annotations

import json
import os
from pathlib import Path

import faiss
import numpy as np

from organizer.database import (
    connect,
    get_embeddable_files,
    mark_embedded,
)
from organizer.embedder import embed_texts
from organizer.logger import get_logger


INDEX_DIR = "vector_store"
INDEX_FILE = "faiss.index"
ID_MAP_FILE = "id_map.json"
META_FILE = "meta.json"
BATCH_SIZE = 256
EMBEDDING_VERSION = 2


def get_vector_dir(base_dir: str | Path | None = None) -> Path:
    if base_dir:
        return Path(base_dir) / INDEX_DIR
    return Path.home() / ".openfileai" / INDEX_DIR


def has_index(vector_dir: str | Path | None = None) -> bool:
    return (get_vector_dir(vector_dir) / INDEX_FILE).exists()


def vector_build_status(
    db_path: str | Path | None = None, vector_dir: str | Path | None = None
) -> dict:
    conn = connect(db_path)
    files = get_embeddable_files(conn)
    conn.close()

    vdir = get_vector_dir(vector_dir)
    index_path = vdir / INDEX_FILE
    id_map_path = vdir / ID_MAP_FILE

    embedded = 0
    if index_path.exists() and id_map_path.exists():
        try:
            id_map = json.loads(id_map_path.read_text(encoding="utf-8"))
            ids_in_index = set(id_map.values())
            embedded = sum(1 for f in files if f["id"] in ids_in_index)
        except (ValueError, OSError):
            embedded = 0

    total = len(files)
    return {
        "total": total,
        "embedded": embedded,
        "remaining": max(total - embedded, 0),
        "complete": index_path.exists() and embedded == total and total > 0,
    }


def _embedding_source(f: dict) -> str:
    content = (f["content_text"] or "").strip()[:2000]
    if content:
        return f"{f['name']}\n{content}"
    return f["name"]


def _save_index_state(
    index: faiss.IndexFlatIP,
    id_map: dict[int, int],
    index_path: Path,
    id_map_path: Path,
    meta_path: Path,
) -> None:
    faiss.write_index(index, str(index_path))
    tmp_path = id_map_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(id_map), encoding="utf-8")
    os.replace(tmp_path, id_map_path)
    meta_path.write_text(json.dumps({"version": EMBEDDING_VERSION}), encoding="utf-8")


def _discard_index(index_path: Path, id_map_path: Path, meta_path: Path | None = None) -> None:
    for p in (index_path, id_map_path, meta_path):
        if p is None:
            continue
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass


def _load_index_state(
    index_path: Path, id_map_path: Path, meta_path: Path, log
) -> tuple[faiss.IndexFlatIP | None, dict[int, int]]:
    if not index_path.exists():
        return None, {}

    version: int | None = None
    if meta_path.exists():
        try:
            version = json.loads(meta_path.read_text(encoding="utf-8")).get("version")
        except (ValueError, OSError):
            version = None

    if version != EMBEDDING_VERSION:
        log.warning(
            "Embedding format changed (v%s -> v%d); rebuilding vector index.",
            version if version is not None else "unknown",
            EMBEDDING_VERSION,
        )
        _discard_index(index_path, id_map_path, meta_path)
        return None, {}

    index = faiss.read_index(str(index_path))
    id_map: dict[int, int] = {}
    if id_map_path.exists():
        try:
            id_map = {
                int(k): v
                for k, v in json.loads(id_map_path.read_text(encoding="utf-8")).items()
            }
        except (ValueError, OSError):
            id_map = {}

    if index.ntotal != len(id_map):
        log.warning(
            "Index/id-map mismatch (%d vs %d); discarding and rebuilding from scratch.",
            index.ntotal,
            len(id_map),
        )
        _discard_index(index_path, id_map_path, meta_path)
        return None, {}

    return index, id_map


def _dedupe_index(
    index: faiss.IndexFlatIP, id_map: dict[int, int]
) -> tuple[faiss.IndexFlatIP, dict[int, int]]:
    seen: set[int] = set()
    keep: list[int] = []
    new_id_map: dict[int, int] = {}
    for pos in range(index.ntotal):
        file_id = id_map.get(pos)
        if file_id is None or file_id in seen:
            continue
        seen.add(file_id)
        keep.append(pos)
        new_id_map[len(new_id_map)] = file_id

    vectors = index.reconstruct_n(0, index.ntotal)[keep].astype(np.float32)
    new_index = faiss.IndexFlatIP(index.d)
    new_index.add(vectors)
    return new_index, new_id_map


def build_index(db_path: str | Path | None = None, vector_dir: str | Path | None = None) -> int:
    log = get_logger()
    conn = connect(db_path)

    vdir = get_vector_dir(vector_dir)
    vdir.mkdir(parents=True, exist_ok=True)
    index_path = vdir / INDEX_FILE
    id_map_path = vdir / ID_MAP_FILE
    meta_path = vdir / META_FILE

    index, id_map = _load_index_state(index_path, id_map_path, meta_path, log)

    if index is not None and len(id_map) != len(set(id_map.values())):
        log.warning(
            "Duplicate vectors found in index (%d entries -> %d unique); keeping first copy.",
            len(id_map),
            len(set(id_map.values())),
        )
        index, id_map = _dedupe_index(index, id_map)
        _save_index_state(index, id_map, index_path, id_map_path, meta_path)

    files = get_embeddable_files(conn)
    if index is not None:
        embedded_ids = set(id_map.values())
        to_embed = [f for f in files if f["id"] not in embedded_ids]
    else:
        to_embed = files

    if not to_embed:
        conn.close()
        if index is None:
            log.info("No files with content to embed.")
            return 0
        log.info("Index up to date: %d vectors.", index.ntotal)
        return index.ntotal

    log.info("Embedding %d files ...", len(to_embed))

    try:
        for start in range(0, len(to_embed), BATCH_SIZE):
            batch = to_embed[start : start + BATCH_SIZE]
            vecs = embed_texts([_embedding_source(f) for f in batch])

            if index is None:
                index = faiss.IndexFlatIP(vecs.shape[1])
            index.add(vecs.astype(np.float32))

            base = index.ntotal - len(batch)
            for j, f in enumerate(batch):
                id_map[base + j] = f["id"]
            mark_embedded(conn, [f["id"] for f in batch])
            conn.commit()

            _save_index_state(index, id_map, index_path, id_map_path, meta_path)

            log.info(
                "  embedded %d / %d ...",
                min(start + BATCH_SIZE, len(to_embed)),
                len(to_embed),
            )
    except KeyboardInterrupt:
        log.info(
            "Build interrupted at %d of %d files. Progress is saved; resume anytime with "
            "`file-organizer index --build-vectors-only`.",
            index.ntotal if index is not None else 0,
            len(to_embed),
        )
        raise

    conn.close()
    log.info("Index built: %d vectors, dim=%d", index.ntotal, index.d)
    return index.ntotal


def search_index(
    query_embedding: np.ndarray,
    limit: int = 10,
    vector_dir: str | Path | None = None,
) -> list[tuple[int, float]]:
    vdir = get_vector_dir(vector_dir)
    index_path = vdir / INDEX_FILE
    map_path = vdir / ID_MAP_FILE

    if not index_path.exists():
        return []

    index = faiss.read_index(str(index_path))
    id_map = json.loads(map_path.read_text(encoding="utf-8"))

    scores, indices = index.search(query_embedding.astype(np.float32), min(limit, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        file_id = id_map.get(str(idx))
        if file_id is not None:
            results.append((file_id, float(score)))

    return results
