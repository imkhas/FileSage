from __future__ import annotations

import logging
import threading
from collections import deque
from pathlib import Path

from organizer.config_loader import load_config
from organizer.indexer import index_folders
from organizer.logger import get_logger
from organizer.search import search
from organizer.smart import analyze, apply_actions
from organizer.sorter import organize, undo
from organizer.utils import generate_summary
from organizer.vector_store import build_index, vector_build_status
from organizer.watcher import start_watching, stop_watching

_ATTACHED_HANDLERS: list[logging.Handler] = []

_MAX_LOG = 5000


class GuiLogHandler(logging.Handler):
    """Forwards 'organizer' logger records to the GUI log sink."""

    def __init__(self, sink: callable) -> None:
        super().__init__(level=logging.INFO)
        self.sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.sink(record.getMessage())
        except Exception:
            pass


def _attach_log_sink(sink: callable) -> None:
    logger = logging.getLogger("organizer")
    for handler in _ATTACHED_HANDLERS:
        logger.removeHandler(handler)
        _ATTACHED_HANDLERS.remove(handler)
    handler = GuiLogHandler(sink)
    logger.addHandler(handler)
    _ATTACHED_HANDLERS.append(handler)


def _smart_report_lines(report) -> list[str]:
    moves = [fs for fs in report.files if fs.category]
    renames = [fs for fs in report.files if fs.new_name]
    lines: list[str] = []
    if not moves and not renames and not report.duplicates:
        lines.append("No suggestions found. Your files look clean.")
        return lines

    if moves:
        lines.append(f"Category suggestions ({len(moves)}):")
        for fs in moves:
            lines.append(f"  {fs.file.name}  ->  {fs.category}/")
    if renames:
        lines.append(f"Rename suggestions ({len(renames)}):")
        for fs in renames:
            lines.append(f"  {fs.file.name}  ->  {fs.new_name}")
    if report.duplicates:
        lines.append(f"Duplicate groups ({len(report.duplicates)}):")
        for group in report.duplicates:
            keep, *rest = sorted(group)
            lines.append(f"  * {keep.name}  (keep)")
            for dup in rest:
                lines.append(f"      {dup.name}  (duplicate)")
    return lines


def _status_text(status: dict) -> str:
    if status["complete"]:
        return (
            f"COMPLETE: {status['embedded']} / {status['total']} files embedded. "
            "Ready to search."
        )
    return (
        f"INCOMPLETE: {status['embedded']} / {status['total']} embedded "
        f"({status['remaining']} remaining). Click 'Build vectors' to resume."
    )


def _format_results(results: list[dict]) -> list[str]:
    lines: list[str] = []
    if not results:
        return ["No results found."]
    lines.append(f"Found {len(results)} result(s):")
    for i, r in enumerate(results, 1):
        lines.append(f"  {i}. {r['name']}  (score: {r.get('score', 0)})")
        lines.append(f"     {r['path']}")
    return lines


class FileSageApi:
    """Bridge exposed to the HTML UI via ``window.pywebview.api``."""

    def __init__(self) -> None:
        self.window = None
        self._logs: deque[tuple[int, str, str, str]] = deque(maxlen=_MAX_LOG)
        self._seq = 0
        self._lock = threading.Lock()
        self._smart_report = None
        self._watching = False

    # ----- log plumbing -----

    def _log(self, panel: str, message: str, cls: str = "") -> None:
        with self._lock:
            self._seq += 1
            self._logs.append((self._seq, panel, str(message), cls))

    def get_logs(self, after: int = 0) -> dict:
        """Return log entries newer than ``after``; used by JS polling."""
        with self._lock:
            entries = [(s, p, m, c) for (s, p, m, c) in self._logs if s > after]
        return {"entries": entries, "next": self._seq}

    # ----- helpers -----

    @staticmethod
    def _config() -> dict:
        return load_config("config.json")

    # ----- folder picker -----

    def pick_folder(self) -> str | None:
        import webview

        window = self.window or (webview.windows[0] if webview.windows else None)
        if window is None:
            return None
        picked = window.create_file_dialog(webview.FOLDER_DIALOG)
        if isinstance(picked, (tuple, list)):
            return picked[0] if picked else None
        return picked

    # ----- organize -----

    def organize(self, path: str, dry_run: bool = False, recursive: bool = False) -> str:
        path = (path or "").strip()
        if not path:
            self._log("organize", "Enter a folder path first.", "dim")
            return "Enter a folder path first."
        self._log("organize", f"Running organize on {path} (dry_run={dry_run})...")
        try:
            results = organize(
                path, self._config(), dry_run=dry_run, recursive=recursive
            )
        except Exception as e:  # noqa: BLE001
            self._log("organize", f"Organize failed: {e}", "primary")
            return f"Organize failed: {e}"
        summary = generate_summary(results)
        self._log("organize", summary, "primary")
        return summary

    def undo(self, path: str) -> int:
        path = (path or "").strip()
        if not path:
            self._log("organize", "Enter a folder path first.", "dim")
            return 0
        try:
            count = undo(path)
        except Exception as e:  # noqa: BLE001
            self._log("organize", f"Undo failed: {e}", "primary")
            return 0
        self._log("organize", f"Undo complete: {count} files restored.", "primary")
        return count

    # ----- smart -----

    def analyze(self, path: str, recursive: bool = False) -> str:
        path = (path or "").strip()
        if not path:
            self._log("smart", "Enter a folder path first.", "dim")
            return "Enter a folder path first."
        self._log("smart", f"Analyzing {path}...")
        try:
            report = analyze(Path(path), self._config(), recursive=recursive)
        except Exception as e:  # noqa: BLE001
            self._log("smart", f"Analysis failed: {e}", "primary")
            return f"Analysis failed: {e}"
        self._smart_report = report
        for line in _smart_report_lines(report):
            self._log("smart", line)
        return f"Analyzed {path}."

    def apply_smart(
        self,
        path: str,
        apply_moves: bool = True,
        apply_renames: bool = True,
        apply_duplicates: bool = True,
    ) -> int:
        report = self._smart_report
        if report is None:
            self._log("smart", "Run 'Analyze' first.", "dim")
            return 0
        try:
            results = apply_actions(
                Path(path),
                report,
                apply_moves=apply_moves,
                apply_renames=apply_renames,
                apply_duplicates=apply_duplicates,
            )
        except Exception as e:  # noqa: BLE001
            self._log("smart", f"Apply failed: {e}", "primary")
            return 0
        applied = sum(1 for r in results if r["status"] == "applied")
        for r in results:
            self._log(
                "smart",
                f"[{r['status']}] {r['action']}: {r['file']} -> {r['detail']}",
            )
        self._log("smart", f"Applied {applied} action(s).", "primary")
        return applied

    # ----- watch -----

    def set_watching(self, path: str, on: bool) -> str:
        if on:
            path = (path or "").strip()
            if not path:
                return "Enter a folder path first."
            if self._watching:
                return "Already watching."
            try:
                start_watching(
                    path,
                    self._config(),
                    on_event=lambda msg: self._log("watch", msg),
                )
            except RuntimeError:
                return "Already watching."
            except Exception as e:  # noqa: BLE001
                return f"Failed to start watching: {e}"
            self._watching = True
            self._log(
                "watch",
                f"Watching {path}... (new files will be organized automatically)",
                "primary",
            )
            return "Watching started."
        if self._watching:
            stop_watching()
            self._watching = False
            self._log("watch", "Stopped watching.", "primary")
            return "Watching stopped."
        return "Not watching."

    def is_watching(self) -> bool:
        return self._watching

    # ----- search -----

    def search(self, query: str, limit: int = 10) -> str:
        query = (query or "").strip()
        if not query:
            self._log("search", "Type a search query first.", "dim")
            return "Type a search query first."
        try:
            results = search(query, limit=limit)
        except Exception as e:  # noqa: BLE001
            self._log("search", f"Search failed: {e}", "primary")
            return f"Search failed: {e}"
        for line in _format_results(results):
            self._log("search", line)
        return f"Found {len(results)} result(s)."

    def index_folder(self, folder: str) -> int:
        folder = (folder or "").strip()
        if not folder:
            self._log("search", "Enter a folder to index.", "dim")
            return 0
        try:
            count = index_folders([folder])
        except Exception as e:  # noqa: BLE001
            self._log("search", f"Indexing failed: {e}", "primary")
            return 0
        self._log("search", f"Indexed {count} files into the database.", "primary")
        return count

    def build_vectors(self) -> int:
        self._log("search", "Building vector index (resumable; progress below)...")
        try:
            count = build_index()
        except Exception as e:  # noqa: BLE001
            self._log("search", f"Vector build failed: {e}", "primary")
            return 0
        self._log("search", f"Vector index built: {count} vectors.", "primary")
        return count

    def index_status(self) -> str:
        try:
            status = vector_build_status()
        except Exception as e:  # noqa: BLE001
            self._log("search", f"Index status failed: {e}", "primary")
            return f"Index status failed: {e}"
        text = _status_text(status)
        self._log("search", text)
        return text


def _load_app() -> Path:
    return Path(__file__).resolve().parent / "webui" / "index.html"


def launch() -> None:
    """Launch the FileSage desktop GUI (pywebview + HTML/CSS)."""
    import webview

    api = FileSageApi()
    _attach_log_sink(lambda msg: api._log("organize", msg))

    window = webview.create_window(
        "FileSage",
        url=_load_app().as_uri(),
        js_api=api,
        width=1120,
        height=760,
        min_size=(900, 600),
        background_color="#121212",
    )
    api.window = window
    webview.start()


if __name__ == "__main__":
    get_logger()
    launch()
