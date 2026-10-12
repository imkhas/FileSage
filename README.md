# FileSage

Privacy-first local AI file intelligence assistant. Organize files by type, get meaning-based suggestions, and search them using natural language — all offline, no data leaves your computer.

FileSage has a **desktop GUI** (click, no terminal needed) and a **command-line interface** (for scripts and servers). Both are completely local.

---

## Features

### Desktop GUI
A dark, tabbed desktop app that covers everything without a terminal: Organize, Smart suggestions, Watch, and Search. On Windows it ships as a self-contained app you double-click — nothing to install. Launch it from the CLI with `file-organizer gui`.

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

### Smart Suggestions (AI)
`smart` understands file meaning, not just extensions. It suggests category moves, clean filenames, and duplicate handling — previewed first, applied only with your approval:

```
file-organizer smart ~/Downloads --dry-run
file-organizer smart ~/Downloads
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

Once folders are indexed, rebuild the vector index from the database without re-scanning. Builds are resumable and self-checkpointing — an interrupted build picks up where it left off:
```
file-organizer index --build-vectors-only
file-organizer index --status
```

Every file is embedded using its **filename plus content**, so search matches by name too — even files with no readable text (videos, archives, binaries) are findable by their filename.

---

## Installation

There are three ways to use FileSage — pick the one that fits you:

| Way | Who it's for | Setup required |
|---|---|---|
| **Windows app (.exe)** | Most people | None |
| **Docker** | Running commands in a terminal, servers, scripts | Docker only |
| **From source / pip** | Developers | Python 3.10+ |

### Option 1 — Windows app (recommended)

Download the latest `FileSage` folder (or its zip) from the GitHub releases page, extract it, and double-click `FileSage.exe`. It opens the desktop GUI. **No Python and no packages to install** — everything is bundled inside the folder.

> Note: the app is built for Windows only. On macOS/Linux, use Option 2 or 3.

### Option 2 — Docker (terminal only)

Run any CLI command in a clean, throwaway container — no Python needed on your machine:

```bash
git clone https://github.com/imkhas/FileSage.git
cd FileSage
docker compose run --rm file-organizer organize /data --dry-run   # preview first
docker compose run --rm file-organizer smart /data --dry-run
docker compose run --rm file-organizer search "invoice"
```

Your `./data` folder is mounted into the container at `/data`. The GUI is not available in Docker (a container has no display) — this is for terminal use, servers, and scripts.

### Option 3 — From source or pip (Python)

Requires **Python 3.10+**. Install the published package:

```bash
pip install file-organizer
```

Or clone and install in editable mode:

```bash
git clone https://github.com/imkhas/FileSage.git
cd FileSage
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -e .
```

> **Linux users:** if `pip install` fails with an `externally-managed-environment` error, use a virtual environment (as above) or `pipx install file-organizer`. To run the GUI on Linux you also need GTK/WebKit2: `sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.1 gir1.2-gtk-3.0`.

---

## Commands

| Command | Description |
|---|---|
| `organize <path>` | Sort files into category folders |
| `organize <path> --dry-run` | Preview without moving |
| `organize <path> --recursive` | Organize files in subdirectories too |
| `watch <path>` | Auto-organize new files |
| `--undo <path>` | Restore files to original locations |
| `index <folders...>` | Scan and index files for semantic search |
| `index <folders...> --build-vectors` | Index and build vector search index |
| `index --build-vectors-only` | Build/resume the vector index from the existing database |
| `index --status` | Check whether the vector index is complete |
| `search <query>` | Search indexed files using natural language |
| `search <query> --limit 20` | Control number of results |
| `smart <path>` | Suggest category moves, renames, and duplicate handling |
| `smart <path> --dry-run` | Preview smart suggestions without changing anything |
| `smart <path> --recursive` | Analyze subdirectories recursively |
| `smart <path> --yes` | Apply all smart suggestions without prompting |
| `gui` | Launch the desktop GUI (organize, smart, watch, search) |

---

## Configuration

Edit `config.json` to customize category rules:

```json
{
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
    "Video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml"],
    "Executables": [".exe", ".sh", ".bat", ".bin"]
}
```

The `smart` command additionally understands meaning-based categories (Finance, Career, Education, ...) — see [`examples/config.custom.json`](examples/config.custom.json).

No code changes needed — just edit the JSON file. When running from source, the config is `config.json` in the project folder; in the Windows app, it's the `config.json` sitting next to `FileSage.exe` (a default is bundled and used if none is present).

---

## Safety

- **Dry-run mode** — shows what will happen before any file moves
- **No overwrites** — duplicate files get numeric suffixes (e.g. `file_1.pdf`)
- **Locked files** — files in use are safely skipped
- **Undo** — every organize creates an undo log to reverse changes
- **Index-only** — search index is read-only, never modifies files
- **100% offline** — all AI processing runs locally, no data uploaded

---

## Documentation

- [Quickstart](docs/quickstart.md) — install and first commands
- [Command Reference](COMMANDS.md) — every command, flag, and example
- [Architecture](docs/architecture.md) — module overview and data flow
- [Development](docs/development.md) — setup, tests, CI, building, releasing
- [Contributing](CONTRIBUTING.md) — how to help

## Examples

See [`examples/`](examples/) for a custom meaning-based `config.json` and programmatic usage.

---

## Project Structure

```
FileSage/
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
│   ├── search.py           # Natural language search
│   ├── renamer.py          # Clean filename suggestions
│   ├── duplicate_detector.py # Content/visual duplicate detection
│   ├── smart.py            # AI category + rename + duplicate suggestions
│   ├── gui.py              # pywebview desktop GUI entry point
│   └── webui/              # HTML/CSS/JS interface for the GUI
│       ├── index.html
│       ├── style.css
│       └── app.js
├── tests/
│   ├── test_sorter.py
│   ├── test_config.py
│   ├── test_duplicates.py
│   ├── test_cli.py
│   ├── test_extractor.py
│   ├── test_renamer.py
│   ├── test_duplicate_detector.py
│   ├── test_smart.py
│   ├── test_embedder.py
│   ├── test_vector_store.py
│   ├── test_search.py
│   └── test_gui.py
├── config.json
├── main.py                # Alternative CLI entry (python main.py)
├── docs/                  # User + architecture documentation
├── examples/              # Sample configs and usage
├── launcher.py            # Frozen GUI entry point (used by PyInstaller)
├── FileSage.spec          # PyInstaller build config (Windows exe)
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── CONTRIBUTING.md
├── pyproject.toml
└── README.md
```

---

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

### Building the Windows exe

```bash
pip install -e ".[dev]"
python -m PyInstaller FileSage.spec --noconfirm
# output: dist\FileSage\FileSage.exe  (a folder; zip it for distribution)
```

---

## How It Works

**Organization:** Files are scanned recursively, categorized by extension using `config.json` rules, and moved into category folders. Every move is logged and recorded in an undo log.

**Smart suggestions:** Each file's name plus its extracted text is embedded with the same local model and compared against meaning-based category anchors (cosine similarity). Matches above a confidence threshold are suggested as category moves; otherwise the extension rules apply. Clean-name and duplicate suggestions are added on top.

**Search:** Files are indexed by extracting text content (PDF, DOCX, code, etc.) and embedding each file's **filename plus content** using a local sentence-transformer model, so files are findable by name even when no text can be extracted. Queries are embedded the same way and matched using FAISS similarity search. Embedding is batched, checkpointed to disk after every batch, and resumable — rerunning `index --build-vectors-only` continues from the last checkpoint. Everything runs on your machine — no external APIs.

---

## License

MIT — see [LICENSE](LICENSE).
