# Architecture

FileSage is a Python application with a **CLI** and a **desktop GUI**, built around three capabilities: **organizing**, **smart suggestions**, and **semantic search**. Everything runs locally.

```
          file-organizer (CLI)        FileSage.exe (frozen GUI)
                 |                            |
                 +-------------+--------------+
                               |
                    organizer/ (shared core)
                               |
        +----------------------+-------------------+
        |                      |                   |
   organize/undo          smart suggestions    index / search
   (sorter)              (smart + renamer +    (indexer ->
        |                 duplicate_detector)    embedder ->
        |                      |                 vector_store ->
   watcher                semantic model        search)
```

## Modules

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing and command dispatch |
| `gui.py` | pywebview desktop GUI (`FileSageApi` bridge + `launch()`) |
| `webui/` | HTML/CSS/JS frontend for the GUI |
| `launcher.py` | Frozen GUI entry point used by the PyInstaller build |
| `config_loader.py` | Loads and validates `config.json` category rules |
| `sorter.py` | Scans, categorizes by extension, moves files, undo logs |
| `duplicate_handler.py` | Collision-safe destination resolution (`file_1.pdf`) |
| `watcher.py` | Real-time folder monitoring (watchdog) |
| `database.py` | SQLite metadata store (`file_index.db`), tracks per-file embedding state (`embedded_at`) |
| `extractor.py` | Text extraction: PDF (PyMuPDF), DOCX, OCR (Tesseract), code/plain text |
| `indexer.py` | Recursive scan and content indexing pipeline |
| `embedder.py` | Local embeddings via `all-MiniLM-L6-v2` (silences model download noise) |
| `vector_store.py` | FAISS vector index + id mapping; batched, checkpointed, resumable builds with duplicate self-repair |
| `search.py` | Natural-language search over the vector index |
| `renamer.py` | Clean filename suggestions (strips `_v3`, `_final`, `(1)`, ...) |
| `duplicate_detector.py` | Exact (SHA-256), image perceptual (dhash), and text near-duplicate detection |
| `smart.py` | Semantic category suggestions (embedding-based classifier) + approval-based apply flow |

## Data flow

**Search:** files → text extraction → embeddings → FAISS index → similarity ranking.

Every file is embedded using its **filename plus extracted text** (`name\ncontent`), so results match on either the name or the content. Files with no extractable text (videos, archives, binaries, images OCR can't read) are still embedded by filename alone, making every indexed file searchable.

Vector builds are resumable: embeddings are computed in batches of 256, written to disk (`faiss.index` + `id_map.json`) after every batch, and per-file embedding state is stored in the database. The `id_map` is the source of truth for what is embedded, so reruns only embed genuinely new files and duplicate entries are auto-repaired via vector reconstruction. A `meta.json` stores the embedding format version — when the embedding source changes, the index is detected as stale and rebuilt automatically.

**Smart:** files → `name + text` embeddings → cosine similarity against category anchors (keywords + config categories) → category / rename / duplicate suggestions → user approval → actions.

`smart.py` embeds each file (name + extracted text) and compares it against the built-in meaning categories (Finance, Career, Education, ...) plus any extra categories from `config.json`, using a `SemanticCategorizer` with batched `best_many()` comparisons. A match above the confidence threshold wins; otherwise the extension rules from `config.json` are the fallback. Classification runs entirely on the local model — no network calls.

## Storage locations

| Artifact | Default location |
|---|---|
| SQLite index | `~/.openfileai/file_index.db` |
| FAISS vectors | `~/.openfileai/vector_store/faiss.index` |
| Vector id mapping | `~/.openfileai/vector_store/id_map.json` |
| Embedding format version | `~/.openfileai/vector_store/meta.json` |
| Undo logs | `.undo_<timestamp>.jsonl` in the organized folder |
| Logs | `logs/` (project dir) |

## Safety guarantees

- Read-only scanning by default; moves only happen on explicit commands
- Duplicate/rename/category actions require user approval
- Undo logs restore every `organize`
- No network calls: no cloud APIs, no telemetry, no data upload
