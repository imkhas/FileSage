from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from organizer.duplicate_detector import find_duplicates
from organizer.duplicate_handler import resolve_destination
from organizer.embedder import embed_texts
from organizer.extractor import extract_text
from organizer.logger import get_logger
from organizer.renamer import suggest_name
from organizer.sorter import categorize_file, scan_directory
from organizer.utils import ensure_directory, safe_move

KEYWORDS: dict[str, list[str]] = {
    "Finance": [
        "invoice", "receipt", "payment", "salary", "pay slip", "payroll", "tax",
        "bank", "budget", "expense", "bill", "statement", "refund", "purchase",
        "transaction", "money",
    ],
    "Career": [
        "resume", "cv", "cover letter", "application", "interview", "job offer",
        "offer letter", "hiring", "recruitment", "internship", "reference",
    ],
    "Education": [
        "lecture", "notes", "assignment", "syllabus", "exam", "homework", "course",
        "thesis", "dissertation", "textbook", "study", "school", "university", "class",
    ],
    "Projects": [
        "report", "proposal", "requirements", "specification", "design", "architecture",
        "dataset", "experiment", "benchmark", "prototype", "roadmap", "whitepaper", "demo",
    ],
    "Personal": [
        "passport", "identity", "license", "insurance", "certificate", "medical",
        "appointment", "vaccination", "birth certificate", "marriage",
    ],
    "Legal": [
        "contract", "agreement", "terms", "policy", "notice", "disclosure", "waiver",
        "lease", "non-disclosure", "nda",
    ],
}

_SEMANTIC_THRESHOLD = 0.18

_categorizer_lock = threading.Lock()
_categorizer_cache: dict[tuple[str, ...], "SemanticCategorizer"] = {}


class SemanticCategorizer:
    def __init__(self, categories: list[str]) -> None:
        self.categories = categories
        self._vectors = embed_texts([self._anchor(c) for c in categories])

    @staticmethod
    def _anchor(category: str) -> str:
        words = KEYWORDS.get(category, [])[:8]
        if words:
            return f"{category}: {', '.join(words)}"
        return category

    def best(self, text: str) -> tuple[str | None, float]:
        return self.best_many([text])[0]

    def best_many(self, texts: list[str]) -> list[tuple[str | None, float]]:
        results: list[tuple[str | None, float]] = []
        for start in range(0, len(texts), 512):
            batch = texts[start : start + 512]
            vectors = embed_texts(batch)
            scores = vectors @ self._vectors.T
            best_indices = np.argmax(scores, axis=1)
            best_scores = scores[np.arange(len(batch)), best_indices]
            for i, idx in enumerate(best_indices):
                score = float(best_scores[i])
                if score >= _SEMANTIC_THRESHOLD:
                    results.append((self.categories[int(idx)], score))
                else:
                    results.append((None, score))
        return results


def _get_categorizer(categories: list[str]) -> SemanticCategorizer:
    key = tuple(sorted(categories))
    with _categorizer_lock:
        if key not in _categorizer_cache:
            _categorizer_cache[key] = SemanticCategorizer(list(key))
        return _categorizer_cache[key]


def suggest_category(file: Path, config: dict[str, list[str]]) -> str | None:
    base = categorize_file(file, config)
    categorizer = _get_categorizer(list(KEYWORDS))
    best, score = categorizer.best(f"{file.name}\n{extract_text(file)}")
    if best is not None:
        return best
    return base


@dataclass
class FileSuggestion:
    file: Path
    category: str | None = None
    new_name: str | None = None


@dataclass
class SmartReport:
    files: list[FileSuggestion] = field(default_factory=list)
    duplicates: list[list[Path]] = field(default_factory=list)


def analyze(
    path: str | Path,
    config: dict[str, list[str]],
    recursive: bool = False,
) -> SmartReport:
    root = Path(path)
    files = scan_directory(root, recursive=recursive)
    report = SmartReport()

    categorizer = _get_categorizer(list(KEYWORDS))
    texts = [f"{f.name}\n{extract_text(f)}" for f in files]
    semantic = categorizer.best_many(texts)

    for f, (best, _score) in zip(files, semantic):
        category = best if best is not None else categorize_file(f, config)
        if category and f.parent.resolve() == (root / category).resolve():
            category = None

        new_name = suggest_name(f)
        if new_name and new_name == f.name:
            new_name = None

        if category or new_name:
            report.files.append(
                FileSuggestion(file=f, category=category, new_name=new_name)
            )

    report.duplicates = find_duplicates(files)
    return report


def apply_actions(
    root: Path,
    report: SmartReport,
    apply_moves: bool = True,
    apply_renames: bool = True,
    apply_duplicates: bool = True,
    dry_run: bool = False,
) -> list[dict]:
    log = get_logger()
    results: list[dict] = []

    dup_keep: set[Path] = set()
    dup_targets: set[Path] = set()
    for group in report.duplicates:
        keep, *rest = sorted(group)
        dup_keep.add(keep)
        dup_targets.update(rest)

    dup_dir = (
        ensure_directory(root / "Duplicates")
        if (apply_duplicates and not dry_run)
        else None
    )

    suggestions_by_path = {fs.file: fs for fs in report.files}
    all_files: list[FileSuggestion] = []
    seen: set[Path] = set()
    for group in report.duplicates:
        for p in sorted(group):
            if p not in seen:
                seen.add(p)
                all_files.append(suggestions_by_path.get(p) or FileSuggestion(file=p))
    for fs in report.files:
        if fs.file not in seen:
            seen.add(fs.file)
            all_files.append(fs)

    for fs in all_files:
        current = fs.file

        if fs.file in dup_targets and apply_duplicates:
            if dup_dir is None:
                dest = root / "Duplicates" / current.name
            else:
                dest = resolve_destination(dup_dir, current.name)
            if dry_run:
                results.append({
                    "action": "duplicate",
                    "file": str(current),
                    "detail": f"Would move to {dest}",
                    "status": "pending",
                })
                continue
            try:
                safe_move(current, dest)
                results.append({
                    "action": "duplicate",
                    "file": str(current),
                    "detail": str(dest),
                    "status": "applied",
                })
            except Exception as e:
                results.append({
                    "action": "duplicate",
                    "file": str(current),
                    "detail": str(e),
                    "status": "error",
                })
            continue

        if apply_renames and fs.new_name:
            dest = current.with_name(fs.new_name)
            if dest.exists():
                results.append({
                    "action": "rename",
                    "file": str(current),
                    "detail": f"Target exists, skipped: {dest.name}",
                    "status": "skipped",
                })
            elif dry_run:
                results.append({
                    "action": "rename",
                    "file": str(current),
                    "detail": f"Would rename to {fs.new_name}",
                    "status": "pending",
                })
            else:
                try:
                    safe_move(current, dest)
                    results.append({
                        "action": "rename",
                        "file": str(current),
                        "detail": fs.new_name,
                        "status": "applied",
                    })
                    current = dest
                except Exception as e:
                    results.append({
                        "action": "rename",
                        "file": str(current),
                        "detail": str(e),
                        "status": "error",
                    })

        if apply_moves and fs.category:
            if dry_run:
                results.append({
                    "action": "move",
                    "file": str(current),
                    "detail": f"Would move to {root / fs.category / current.name}",
                    "status": "pending",
                })
                continue
            target = ensure_directory(root / fs.category)
            dest = resolve_destination(target, current.name)
            try:
                safe_move(current, dest)
                results.append({
                    "action": "move",
                    "file": str(current),
                    "detail": str(dest),
                    "status": "applied",
                })
            except Exception as e:
                results.append({
                    "action": "move",
                    "file": str(current),
                    "detail": str(e),
                    "status": "error",
                })

    return results


def print_report(report: SmartReport) -> None:
    moves = [fs for fs in report.files if fs.category]
    renames = [fs for fs in report.files if fs.new_name]

    if not moves and not renames and not report.duplicates:
        print("No suggestions found. Your files look clean.")
        return

    if moves:
        print("Category suggestions:")
        for i, fs in enumerate(moves, 1):
            print(f"  {i}. {fs.file.name}  ->  {fs.category}/")
        print()

    if renames:
        print("Rename suggestions:")
        for i, fs in enumerate(renames, 1):
            print(f"  {i}. {fs.file.name}  ->  {fs.new_name}")
        print()

    if report.duplicates:
        print("Duplicate groups:")
        for group in report.duplicates:
            keep, *rest = sorted(group)
            print(f"  * {keep.name}  (keep)")
            for dup in rest:
                print(f"      {dup.name}  (duplicate)")
        print()
