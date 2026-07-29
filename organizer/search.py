from __future__ import annotations

from organizer.database import connect
from organizer.embedder import embed_query
from organizer.vector_store import search_index


def search(query: str, limit: int = 10, db_path: str | None = None) -> list[dict]:
    conn = connect(db_path)
    query_vec = embed_query(query)
    results = search_index(query_vec, limit=limit)

    if not results:
        conn.close()
        return []

    file_ids = [r[0] for r in results]
    scores = {r[0]: r[1] for r in results}

    placeholders = ",".join("?" * len(file_ids))
    rows = conn.execute(
        f"SELECT * FROM files WHERE id IN ({placeholders})", file_ids
    ).fetchall()
    conn.close()

    files = {row["id"]: dict(row) for row in rows}

    ranked = []
    for fid in file_ids:
        if fid in files:
            entry = files[fid]
            entry["score"] = round(scores[fid], 4)
            ranked.append(entry)

    return ranked
