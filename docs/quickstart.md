# Quickstart

## Install

Requires **Python 3.10+**.

```bash
pip install file-organizer
```

Or install from source:

```bash
git clone https://github.com/imkhas/FileSage.git
cd FileSage
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

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

## Full command reference

See [COMMANDS.md](../COMMANDS.md) for every command, flag, and example.
