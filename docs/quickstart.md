# Quickstart

## Choose how you run FileSage

| Way | Setup required | Who it's for |
|---|---|---|
| **Windows app (.exe)** | None | Most people |
| **Docker** | Docker only | Terminal use, servers, scripts |
| **From source / pip** | Python 3.10+ | Developers |

### Windows app (recommended)

Download the `FileSage` folder (or its zip) from the GitHub releases page, extract it, and double-click `FileSage.exe`. The desktop GUI opens — organize, smart suggestions, watch, and search are all available without a terminal.

### Docker (terminal only)

```bash
git clone https://github.com/imkhas/FileSage.git
cd FileSage
docker compose run --rm file-organizer organize /data --dry-run   # preview first
```

Your `./data` folder is mounted into the container at `/data`.

### From source / pip

```bash
git clone https://github.com/imkhas/FileSage.git
cd FileSage
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

Or install the published package with `pip install file-organizer`. On Linux, a failing `pip install` usually means you need a virtual environment (above) or `pipx`; for the GUI, also install GTK/WebKit2 (`gir1.2-webkit2-4.1` and friends).

All commands below use `file-organizer` — the same command works after a pip install or inside Docker (e.g. `docker compose run --rm file-organizer organize /data`).

## 1. Organize a folder

Preview first (never moves anything):

```bash
file-organizer organize ~/Downloads --dry-run
```

Then run for real:

```bash
file-organizer organize ~/Downloads
```

Restore if you change your mind:

```bash
file-organizer --undo ~/Downloads
```

## 2. Smart suggestions (AI)

FileSage suggests meaning-based categories, clean filenames, and duplicate files. Nothing is modified without your approval:

```bash
file-organizer smart ~/Downloads --dry-run
file-organizer smart ~/Downloads
```

## 3. Semantic search

Index your folders, then ask natural-language questions:

```bash
file-organizer index ~/Documents ~/Projects
file-organizer index --build-vectors-only
file-organizer search "my internship documents"
file-organizer search "invoice" --limit 5
```

`index --build-vectors-only` builds the vector embeddings from the already-indexed database — no need to re-scan folders. Vector builds are resumable and checkpointed every batch, so an interrupted build can be continued by simply rerunning the same command. Check progress any time:

```bash
file-organizer index --status
```

## 4. Watch a folder

Auto-organize new files as they appear:

```bash
file-organizer watch ~/Downloads
```

## 5. Desktop GUI

```bash
file-organizer gui
```

Opens the desktop window (Organize, Smart, Watch, Search tabs). On Windows, prefer the bundled app from Option 1.

## Full command reference

See [COMMANDS.md](../COMMANDS.md) for every command, flag, and example.
