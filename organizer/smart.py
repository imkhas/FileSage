from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from organizer.duplicate_detector import find_duplicates
from organizer.duplicate_handler import resolve_destination
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

_CATEGORY_SCORE_THRESHOLD = 3
_NAME_KEYWORD_WEIGHT = 3


def _keyword_hits(text: str) -> dict[str, int]:
    lower = re.sub(r"[-_/\\]+", " ", text).lower()
    hits: dict[str, int] = {}
    for cat, words in KEYWORDS.items():
        score = 0
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", lower):
                score += 1
        if score:
            hits[cat] = score
    return hits


def suggest_category(file: Path, config: dict[str, list[str]]) -> str | None:
    base = categorize_file(file, config)

    name_hits: dict[str, int] = {}
    name_tokens = re.split(r"[-_.\s]+", file.stem)
    for cat, words in KEYWORDS.items():
        score = 0
        for word in words:
            if any(
                token.lower() == word or token.lower().startswith(word)
                for token in name_tokens
                if token
            ):
                score += _NAME_KEYWORD_WEIGHT
        if score:
            name_hits[cat] = score

    content_hits = _keyword_hits(extract_text(file))

    combined: dict[str, int] = {}
    for cat in KEYWORDS:
        combined[cat] = name_hits.get(cat, 0) + content_hits.get(cat, 0)

    best, best_score = None, 0
    for cat, score in combined.items():
        if score > best_score:
            best, best_score = cat, score

    if best_score >= _CATEGORY_SCORE_THRESHOLD:
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

    for f in files:
        category = suggest_category(f, config)
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
