from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from organizer.database import connect, get_files_without_embeddings
from organizer.embedder import embed_texts
from organizer.logger import get_logger


INDEX_DIR = "vector_store"
INDEX_FILE = "faiss.index"
ID_MAP_FILE = "id_map.json"


def get_vector_dir(base_dir: str | Path | None = None) -> Path:
    if base_dir:
        return Path(base_dir) / INDEX_DIR
    return Path.home() / ".openfileai" / INDEX_DIR


def build_index(db_path: str | Path | None = None, vector_dir: str | Path | None = None) -> int:
    log = get_logger()
    conn = connect(db_path)
    files = get_files_without_embeddings(conn)
    conn.close()

    if not files:
        log.info("No files with content to embed.")
        return 0

    log.info("Embedding %d files ...", len(files))

    texts = [f["content_text"][:2000] for f in files]
    embeddings = embed_texts(texts)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype(np.float32))

    vdir = get_vector_dir(vector_dir)
    vdir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(vdir / INDEX_FILE))

    id_map = {i: files[i]["id"] for i in range(len(files))}
    (vdir / ID_MAP_FILE).write_text(json.dumps(id_map), encoding="utf-8")

    log.info("Index built: %d vectors, dim=%d", len(files), dim)
    return len(files)


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
