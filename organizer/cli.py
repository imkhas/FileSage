from __future__ import annotations

import argparse
import signal
import sys

from organizer.config_loader import load_config
from organizer.logger import get_logger, setup_logger
from organizer.sorter import organize, undo
from organizer.utils import generate_summary
from organizer.watcher import start_watching, stop_watching


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-organizer",
        description="AI-powered file organizer with semantic search",
    )

    parser.add_argument(
        "--undo",
        type=str,
        metavar="PATH",
        help="Undo a previous organize in the given directory",
    )

    sub = parser.add_subparsers(dest="command")

    org = sub.add_parser("organize", help="Organize files in a directory")
    org.add_argument("path", type=str, help="Directory to organize")
    org.add_argument("--dry-run", action="store_true", help="Simulate without moving files")

    watch = sub.add_parser("watch", help="Watch a directory and auto-organize")
    watch.add_argument("path", type=str, help="Directory to watch")

    idx = sub.add_parser("index", help="Index folders for semantic search")
    idx.add_argument("folders", type=str, nargs="+", help="Folders to index")
    idx.add_argument("--build-vectors", action="store_true", help="Also build vector index")

    search = sub.add_parser("search", help="Search indexed files using natural language")
    search.add_argument("query", type=str, help="Natural language search query")
    search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    return parser


def main() -> None:
    setup_logger()
    log = get_logger()
    parser = build_parser()
    args = parser.parse_args()

    if args.undo:
        count = undo(args.undo)
        log.info("Undo complete: %d files restored", count)
        return

    if args.command == "watch":
        config = load_config("config.json")
        start_watching(args.path, config)

        def _stop(_signo, _frame):
            log.info("Shutting down watcher...")
            stop_watching()
            sys.exit(0)

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)
        log.info("Watching %s (Ctrl+C to stop)...", args.path)
        signal.pause()

    if args.command == "organize":
        config = load_config("config.json")
        results = organize(args.path, config, dry_run=args.dry_run)
        print(generate_summary(results))
        return

    if args.command == "index":
        from organizer.indexer import index_folders
        from organizer.vector_store import build_index

        count = index_folders(args.folders)
        print(f"Indexed {count} files.")

        if args.build_vectors:
            vcount = build_index()
            print(f"Built vector index: {vcount} vectors.")
        return

    if args.command == "search":
        from organizer.search import search as do_search

        results = do_search(args.query, limit=args.limit)
        if not results:
            print("No results found.")
            return

        print(f"Found {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            score = r.get("score", 0)
            print(f"  {i}. {r['name']}")
            print(f"     Path: {r['path']}")
            print(f"     Score: {score}")
            print()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
