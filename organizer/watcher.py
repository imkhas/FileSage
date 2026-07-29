from __future__ import annotations

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from organizer.duplicate_handler import resolve_destination
from organizer.logger import get_logger
from organizer.sorter import categorize_file
from organizer.utils import ensure_directory, is_locked, safe_move

_OBSERVER: Observer | None = None


class OrganizerHandler(FileSystemEventHandler):
    def __init__(self, config: dict[str, list[str]]) -> None:
        self.config = config
        self.log = get_logger()
        self._recent: set[str] = set()

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        if not src.exists() or is_locked(src):
            return

        key = str(src)
        if key in self._recent:
            return
        self._recent.add(key)

        category = categorize_file(src, self.config)
        if category is None:
            self.log.debug("No category for %s", src.name)
            return

        category_dir = ensure_directory(src.parent / category)
        try:
            dest = resolve_destination(category_dir, src.name)
        except Exception as e:
            self.log.error("Failed to resolve destination for %s: %s", src.name, e)
            return

        try:
            safe_move(src, dest)
            self.log.info("Watch: moved %s -> %s", src.name, category)
        except Exception as e:
            self.log.error("Watch: failed to move %s: %s", src.name, e)
        finally:
            self._recent.discard(key)


def start_watching(path: str | Path, config: dict[str, list[str]]) -> None:
    global _OBSERVER
    if _OBSERVER is not None:
        raise RuntimeError("Already watching")

    log = get_logger()
    target = Path(path).resolve()
    log.info("Starting watch on %s", target)

    handler = OrganizerHandler(config)
    observer = Observer()
    observer.schedule(handler, str(target), recursive=False)
    observer.start()
    _OBSERVER = observer


def stop_watching() -> None:
    global _OBSERVER
    if _OBSERVER is None:
        return
    _OBSERVER.stop()
    _OBSERVER.join()
    _OBSERVER = None
