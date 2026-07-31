# FileSage Command Reference Guide

This document lists all available CLI commands for **FileSage / OpenFileAI**, their exact usage syntax, flags, and detailed explanations of what each command does.

> **Note:** In the examples below, replace `<PATH>` (and `<PATH1>`, `<PATH2>`, ...) with the actual folder(s) you want to work on, e.g. `~/Downloads` or `D:\Documents`.

---

## 1. Setup & Maintenance Commands

### Install / Reinstall FileSage
```powershell
python -m pip install -e ".[dev]"
```
- **Description:** Installs FileSage in editable mode along with development dependencies (`pytest`, `torch`, `sentence-transformers`, `faiss-cpu`, etc.).
- **When to use:** Run once when first setting up the project or after cloning.

### Run Unit Tests
```powershell
python -m pytest -v
```
- **Description:** Runs all automated unit tests across `sorter`, `config`, `duplicates`, `cli`, `extractor`, `renamer`, `duplicate_detector`, and `smart` to verify system health.
- **When to use:** Anytime you make code changes or want to ensure everything is working cleanly.

---

## 2. File Organizer Commands (`organize`)

### Preview Organization (Safe Simulation)
```powershell
file-organizer organize <PATH> --dry-run
```
- **Description:** Simulates organizing the folder and displays a summary of what *would* be moved without making any changes to your files or folders on disk.
- **When to use:** Always run this first to preview changes before actual organization.

### Organize Loose Top-Level Files (Default)
```powershell
file-organizer organize <PATH>
```
- **Description:** Scans **only top-level files** sitting directly in `Downloads/` and moves them into category folders (e.g. `Images/`, `Documents/`, `Code/`). **Leaves all existing subfolders, unzipped project folders, and code repositories completely untouched.**
- **When to use:** To clean up cluttered loose files in your Downloads or Desktop folder.

### Organize Files Recursively (Includes Subfolders)
```powershell
file-organizer organize <PATH> --recursive
```
- **Description:** Scans the folder **and all nested subdirectories recursively**, moving matched files out of subfolders into category folders.
- **When to use:** When you want a thorough deep-clean of all nested folders.

### Undo Last Organization
```powershell
file-organizer --undo <PATH>
```
- **Description:** Reads the latest auto-generated undo log (`.undo_<timestamp>.jsonl`) and **restores all moved files back to their exact original locations and folder structure**.
- **When to use:** Anytime you want to reverse a previous `organize` action.

---

## 3. Real-Time Folder Watcher (`watch`)

### Auto-Organize New Files in Real Time
```powershell
file-organizer watch <PATH>
```
- **Description:** Runs a background monitor on the specified directory. Any new file saved or downloaded into the folder will automatically be organized into its proper category folder. Press `Ctrl+C` to stop watching.
- **When to use:** Keep running in a terminal session to keep your Downloads folder permanently clean.

---

## 4. Local AI & Semantic Search Commands (`index` & `search`)

### Scan and Index Folders into Database
```powershell
file-organizer index <PATH1> <PATH2>
```
- **Description:** Recursively scans folders and extracts text content from PDFs, Word docs (`.docx`), plain text, and code files into the local SQLite database. **100% read-only — does NOT move or modify any files.**
- **When to use:** To prepare files for search indexing.

### Build AI Vector Index for Natural Language Search
```powershell
file-organizer index <PATH> --build-vectors
```
- **Description:** Indexes files AND generates local vector embeddings (`all-MiniLM-L6-v2`) saved to a local FAISS vector database.
- **When to use:** Run when you want to enable semantic search on your indexed documents.

### Rebuild Vector Index from Existing Database
```powershell
file-organizer index --build-vectors-only
```
- **Description:** Builds the FAISS vector index directly from the already-indexed SQLite database, **without re-scanning any folders**. Use this after an interrupted build — it resumes from the last checkpoint instead of restarting, so you only embed the files that are still missing.
- **When to use:** When your folders are already indexed (from a previous `index <PATH>` run) but the vector index is missing or incomplete.

### Check Vector Index Build Status
```powershell
file-organizer index --status
```
- **Description:** Shows how many files are embeddable, how many are already embedded, how many remain, and whether the vector index is complete — without running anything.
- **When to use:** After a timed-out or interrupted build, to check whether it finished or if you need to run `--build-vectors-only` again to resume.

### Natural Language Search
```powershell
file-organizer search "my internship offer letter"
```
- **Description:** Queries the FAISS vector index using natural language and returns the top matching files ranked by relevance score.
- **When to use:** Find files based on context or meaning, even if you don't remember the exact filename.

### Natural Language Search with Result Limit
```powershell
file-organizer search "invoice" --limit 5
```
- **Description:** Performs natural language search and limits the output to the top N results (default is 10).
- **When to use:** To narrow down search output when querying broad topics.

---

## 5. Smart Organization Commands (`smart`)

### Preview Smart Suggestions (Safe Simulation)
```powershell
file-organizer smart <PATH> --dry-run
```
- **Description:** Analyzes the folder and lists AI-powered suggestions without changing anything. Reports:
  - **Category moves** — files suggested for a meaning-based folder (e.g. `invoice123.pdf -> Finance/`, `resume.pdf -> Career/`)
  - **Renames** — cleaned-up filenames (e.g. `resume_final_latest_v3.pdf -> resume.pdf`)
  - **Duplicates** — groups of identical or near-identical files
- **When to use:** Always run this first to review what will be suggested.

### Apply Smart Suggestions (With Approval Prompts)
```powershell
file-organizer smart <PATH>
```
- **Description:** Shows suggestions then asks for approval per action type before moving, renaming, or quarantining duplicates into a `Duplicates/` folder. **Nothing is modified without your confirmation.**
- **When to use:** To apply the recommended cleanup safely.

### Apply All Suggestions Without Prompting
```powershell
file-organizer smart <PATH> --yes
```
- **Description:** Applies all suggested category moves, renames, and duplicate moves immediately without asking.
- **When to use:** When you have already previewed the results with `--dry-run` and trust the suggestions.

### Analyze Recursively
```powershell
file-organizer smart <PATH> --recursive
```
- **Description:** Analyzes the folder and all nested subdirectories.
- **When to use:** For a full cleanup pass across nested folders.
