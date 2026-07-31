from __future__ import annotations

import sqlite3
from pathlib import Path

DB_NAME = "file_index.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    extension TEXT,
    size INTEGER,
    modified REAL,
    category TEXT,
    content_text TEXT,
    indexed_at REAL,
    embedded_at REAL
);

CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(files)").fetchall()}
    if "embedded_at" not in cols:
        conn.execute("ALTER TABLE files ADD COLUMN embedded_at REAL")
        conn.commit()


def get_db_path(base_dir: str | Path | None = None) -> Path:
    if base_dir:
        return Path(base_dir) / DB_NAME
    return Path.home() / ".openfileai" / DB_NAME


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def upsert_file(conn: sqlite3.Connection, file_data: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO files (path, name, extension, size, modified, category, content_text, indexed_at)
        VALUES (:path, :name, :extension, :size, :modified, :category, :content_text, :indexed_at)
        ON CONFLICT(path) DO UPDATE SET
            name=excluded.name,
            extension=excluded.extension,
            size=excluded.size,
            modified=excluded.modified,
            category=excluded.category,
            content_text=excluded.content_text,
            indexed_at=excluded.indexed_at
        """,
        file_data,
    )
    conn.commit()
    return cur.lastrowid


def get_all_files(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM files").fetchall()
    return [dict(row) for row in rows]


def get_files_without_embeddings(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM files
        WHERE content_text IS NOT NULL AND content_text != '' AND embedded_at IS NULL
        ORDER BY id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_embeddable_files(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM files ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def mark_embedded(conn: sqlite3.Connection, ids: list[int]) -> None:
    conn.executemany(
        "UPDATE files SET embedded_at = ? WHERE id = ?",
        [(1, file_id) for file_id in ids],
    )


def reset_embeddings(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE files SET embedded_at = NULL "
        "WHERE content_text IS NOT NULL AND content_text != ''"
    )
    conn.commit()


def search_by_path(conn: sqlite3.Connection, pattern: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM files WHERE path LIKE ?", (f"%{pattern}%",)
    ).fetchall()
    return [dict(row) for row in rows]


def get_file_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]


def delete_all(conn: sqlite3.Connection) -> int:
    cur = conn.execute("DELETE FROM files")
    conn.commit()
    return cur.rowcount
