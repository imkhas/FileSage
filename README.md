# OpenFileAI

Privacy-first local AI file intelligence assistant. Organize files by type and search them using natural language — all offline, no data leaves your computer.

```
file-organizer organize ~/Downloads
file-organizer search "my internship documents"
```

---

## Features

### Smart File Organizer
Sort files into category folders by extension. Configurable rules, dry-run mode, undo support.

```
file-organizer organize ~/Downloads
file-organizer organize ~/Downloads --dry-run
file-organizer --undo ~/Downloads
```

### Real-time Watcher
Auto-organize new files as they appear.

```
file-organizer watch ~/Downloads
```

### Semantic Search (AI)
Index your files and search using natural language. Completely offline using local embeddings.

```
file-organizer index ~/Documents ~/Projects
file-organizer search "machine learning project files"
file-organizer search "invoice" --limit 5
```

Search understands meaning, not just filenames:
```
Search: "my internship documents"
→ internship_offer.pdf  (score: 0.52)
→ resume.pdf            (score: 0.48)
→ interview_notes.txt   (score: 0.31)
```

---

## Install

```bash
pip install file-organizer
```

### From source
```bash
git clone https://github.com/yourusername/OpenFileAI.git
cd OpenFileAI
python -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Commands

| Command | Description |
|---|---|
| `organize <path>` | Sort files into category folders |
| `organize <path> --dry-run` | Preview without moving |
| `watch <path>` | Auto-organize new files |
| `--undo <path>` | Restore files to original locations |
| `index <folders...>` | Scan and index files for semantic search |
| `index <folders...> --build-vectors` | Index and build vector search index |
| `search <query>` | Search indexed files using natural language |
| `search <query> --limit 20` | Control number of results |

---

## Configuration

Edit `config.json` to customize category rules:

```json
{
    "Images": [".jpg", ".jpeg", ".png", ".gif"],
    "Documents": [".pdf", ".docx", ".txt", ".md"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Video": [".mp4", ".avi", ".mkv"],
    "Archives": [".zip", ".tar", ".gz"],
    "Code": [".py", ".js", ".ts", ".html", ".css"],
    "Executables": [".exe", ".sh", ".bat"]
}
```

No code changes needed — just edit the JSON file.

---

## Safety

- **Dry-run mode** — shows what will happen before any file moves
- **No overwrites** — duplicate files get numeric suffixes (e.g. `file_1.pdf`)
- **Locked files** — files in use are safely skipped
- **Undo** — every organize creates an undo log to reverse changes
- **Index-only** — search index is read-only, never modifies files
- **100% offline** — all AI processing runs locally, no data uploaded

---

## Project Structure

```
OpenFileAI/
├── organizer/
│   ├── cli.py              # CLI entry point and argument parsing
│   ├── sorter.py           # Core organize/undo logic
│   ├── config_loader.py    # JSON config loading and validation
│   ├── duplicate_handler.py# Safe file rename (no overwrite)
│   ├── logger.py           # Logging setup
│   ├── utils.py            # Shared helpers
│   ├── watcher.py          # Real-time folder monitoring
│   ├── database.py         # SQLite file metadata store
│   ├── extractor.py        # Text extraction (PDF, DOCX, TXT, code)
│   ├── indexer.py          # File scanning and indexing pipeline
│   ├── embedder.py         # Sentence transformer embeddings
│   ├── vector_store.py     # FAISS vector index management
│   └── search.py           # Natural language search
├── tests/
│   ├── test_sorter.py
│   ├── test_config.py
│   ├── test_duplicates.py
│   └── test_cli.py
├── config.json
├── pyproject.toml
└── README.md
```

---

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

---

## How It Works

**Organization:** Files are scanned recursively, categorized by extension using `config.json` rules, and moved into category folders. Every move is logged and recorded in an undo log.

**Search:** Files are indexed by extracting text content (PDF, DOCX, code, etc.) and converting it to vector embeddings using a local sentence-transformer model. Queries are embedded the same way and matched using FAISS similarity search. Everything runs on your machine — no external APIs.

---

## License

MIT
