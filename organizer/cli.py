from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from organizer.config_loader import load_config
from organizer.logger import get_logger, setup_logger
from organizer.sorter import organize, undo
from organizer.utils import generate_summary
from organizer.watcher import start_watching, stop_watching


def _confirm(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [Y/n] ").strip().lower()
    except EOFError:
        return False
    return answer in ("", "y", "yes")


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
    org.add_argument("--recursive", action="store_true", help="Organize files in subdirectories recursively")

    watch = sub.add_parser("watch", help="Watch a directory and auto-organize")
    watch.add_argument("path", type=str, help="Directory to watch")

    idx = sub.add_parser("index", help="Index folders for semantic search")
    idx.add_argument("folders", type=str, nargs="*", help="Folders to index")
    idx.add_argument("--build-vectors", action="store_true", help="Also build vector index")
    idx.add_argument(
        "--build-vectors-only",
        action="store_true",
        help="Build vector index from the existing database without scanning",
    )
    idx.add_argument(
        "--status",
        action="store_true",
        help="Show vector index build status without running anything",
    )

    search = sub.add_parser("search", help="Search indexed files using natural language")
    search.add_argument("query", type=str, help="Natural language search query")
    search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    smart = sub.add_parser(
        "smart", help="Suggest category moves, renames, and duplicate handling"
    )
    smart.add_argument("path", type=str, help="Directory to analyze")
    smart.add_argument(
        "--recursive", action="store_true", help="Analyze subdirectories recursively"
    )
    smart.add_argument(
        "--dry-run", action="store_true", help="Show suggestions without applying"
    )
    smart.add_argument(
        "--yes", "-y", action="store_true", help="Apply all suggestions without prompting"
    )

    sub.add_parser("gui", help="Launch the desktop GUI")

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
        log.info("Watching %s (Ctrl+C to stop)...", args.path)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Shutting down watcher...")
            stop_watching()
            sys.exit(0)

    if args.command == "organize":
        config = load_config("config.json")
        results = organize(args.path, config, dry_run=args.dry_run, recursive=args.recursive)
        print(generate_summary(results))
        return

    if args.command == "index":
        from organizer.indexer import index_folders
        from organizer.vector_store import build_index, vector_build_status

        if args.status:
            status = vector_build_status()
            print(f"Files to embed:     {status['total']}")
            print(f"Already embedded:   {status['embedded']}")
            print(f"Remaining:          {status['remaining']}")
            if status["complete"]:
                print("Vector index: COMPLETE. Ready for `file-organizer search`.")
            else:
                print(
                    "Vector index: INCOMPLETE.\n"
                    "Resume it with:  file-organizer index --build-vectors-only"
                )
            return

        if args.build_vectors_only:
            vcount = build_index()
            print(f"Built vector index: {vcount} vectors.")
            return

        if not args.folders:
            parser.error("index requires at least one folder unless --build-vectors-only is used")

        count = index_folders(args.folders)
        print(f"Indexed {count} files.")

        if args.build_vectors:
            vcount = build_index()
            print(f"Built vector index: {vcount} vectors.")
        return

    if args.command == "search":
        from organizer.search import search as do_search
        from organizer.vector_store import has_index

        if not has_index():
            print(
                "No vector index found. Build one first:\n"
                '  file-organizer index <PATH> --build-vectors\n'
                "or rebuild from the existing database:\n"
                "  file-organizer index --build-vectors-only"
            )
            return

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

    if args.command == "smart":
        from organizer.smart import analyze, apply_actions, print_report

        config = load_config("config.json")
        root = Path(args.path)
        report = analyze(root, config, recursive=args.recursive)
        print_report(report)

        if args.dry_run:
            print("Dry run complete. No changes were made.")
            return

        n_moves = sum(1 for fs in report.files if fs.category)
        n_renames = sum(1 for fs in report.files if fs.new_name)
        n_dups = sum(len(group) - 1 for group in report.duplicates)

        if not (n_moves or n_renames or n_dups):
            print("Nothing to apply.")
            return

        do_moves = n_moves and (args.yes or _confirm(f"Apply {n_moves} category move(s)?"))
        do_renames = n_renames and (args.yes or _confirm(f"Apply {n_renames} rename(s)?"))
        do_dups = n_dups and (args.yes or _confirm(f"Move {n_dups} duplicate(s) to 'Duplicates/'?"))

        results = apply_actions(
            root,
            report,
            apply_moves=do_moves,
            apply_renames=do_renames,
            apply_duplicates=do_dups,
        )
        for r in results:
            if r["status"] == "applied":
                log.info("%s: %s -> %s", r["action"], r["file"], r["detail"])
        applied = sum(1 for r in results if r["status"] == "applied")
        print(f"\nApplied {applied} action(s).")
        return

    if args.command == "gui":
        from organizer.gui import launch

        launch()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
