# FileSage Command Reference Guide

This document lists all available CLI commands for **FileSage / OpenFileAI**, their exact usage syntax, flags, and detailed explanations of what each command does.

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
- **Description:** Runs all 19 automated unit tests across `sorter`, `config`, `duplicates`, and `cli` to verify system health.
- **When to use:** Anytime you make code changes or want to ensure everything is working cleanly.

---

## 2. File Organizer Commands (`organize`)

### Preview Organization (Safe Simulation)
```powershell
file-organizer organize C:\Users\imran\Downloads --dry-run
```
- **Description:** Simulates organizing the folder and displays a summary of what *would* be moved without making any changes to your files or folders on disk.
- **When to use:** Always run this first to preview changes before actual organization.

### Organize Loose Top-Level Files (Default)
```powershell
file-organizer organize C:\Users\imran\Downloads
```
- **Description:** Scans **only top-level files** sitting directly in `Downloads/` and moves them into category folders (e.g. `Images/`, `Documents/`, `Code/`). **Leaves all existing subfolders, unzipped project folders, and code repositories completely untouched.**
- **When to use:** To clean up cluttered loose files in your Downloads or Desktop folder.

### Organize Files Recursively (Includes Subfolders)
```powershell
file-organizer organize C:\Users\imran\Downloads --recursive
```
- **Description:** Scans the folder **and all nested subdirectories recursively**, moving matched files out of subfolders into category folders.
- **When to use:** When you want a thorough deep-clean of all nested folders.

### Undo Last Organization
```powershell
file-organizer --undo C:\Users\imran\Downloads
```
- **Description:** Reads the latest auto-generated undo log (`.undo_<timestamp>.jsonl`) and **restores all moved files back to their exact original locations and folder structure**.
- **When to use:** Anytime you want to reverse a previous `organize` action.

---

## 3. Real-Time Folder Watcher (`watch`)

### Auto-Organize New Files in Real Time
```powershell
file-organizer watch C:\Users\imran\Downloads
```
- **Description:** Runs a background monitor on the specified directory. Any new file saved or downloaded into the folder will automatically be organized into its proper category folder. Press `Ctrl+C` to stop watching.
- **When to use:** Keep running in a terminal session to keep your Downloads folder permanently clean.

---

## 4. Local AI & Semantic Search Commands (`index` & `search`)

### Scan and Index Folders into Database
```powershell
file-organizer index C:\Users\imran\Documents C:\Users\imran\Downloads
```
- **Description:** Recursively scans folders and extracts text content from PDFs, Word docs (`.docx`), plain text, and code files into the local SQLite database. **100% read-only — does NOT move or modify any files.**
- **When to use:** To prepare files for search indexing.

### Build AI Vector Index for Natural Language Search
```powershell
file-organizer index C:\Users\imran\Documents --build-vectors
```
- **Description:** Indexes files AND generates local vector embeddings (`all-MiniLM-L6-v2`) saved to a local FAISS vector database.
- **When to use:** Run when you want to enable semantic search on your indexed documents.

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
