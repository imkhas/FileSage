from __future__ import annotations

import time
from pathlib import Path

from organizer.database import connect, upsert_file, get_file_count
from organizer.extractor import extract_text
from organizer.logger import get_logger


def index_folders(folders: list[str], db_path: str | Path | None = None) -> int:
    log = get_logger()
    conn = connect(db_path)
    count = 0

    for folder in folders:
        root = Path(folder).expanduser().resolve()
        if not root.is_dir():
            log.warning("Skipping non-directory: %s", root)
            continue

        log.info("Indexing %s ...", root)
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part.startswith(".") for part in file_path.parts):
                continue

            try:
                stat = file_path.stat()
                content = extract_text(file_path)
                file_data = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "extension": file_path.suffix.lower(),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "category": None,
                    "content_text": content,
                    "indexed_at": time.time(),
                }
                upsert_file(conn, file_data)
                count += 1
                if count % 500 == 0:
                    log.info("  indexed %d files ...", count)
            except Exception as e:
                log.warning("Failed to index %s: %s", file_path, e)

    total = get_file_count(conn)
    conn.close()
    log.info("Done. Indexed %d files. Total in database: %d", count, total)
    return count
