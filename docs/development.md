# Development

## Setup

```bash
git clone https://github.com/imkhas/FileSage.git
cd FileSage
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
python -m pytest -v
```

The suite must stay fast and offline. The sentence-transformer model and FAISS are mocked in tests (`test_embedder.py`, `test_vector_store.py`, `test_search.py`) so no model download ever happens.

## CI

`.github/workflows/ci.yml` runs the full test suite on push and pull requests to `main` (Python 3.11, Ubuntu).

## Building the Windows exe

FileSage ships as a self-contained Windows app built with PyInstaller:

```bash
python -m PyInstaller FileSage.spec --noconfirm
# output: dist\FileSage\FileSage.exe  (a folder — zip it for distribution)
```

The spec (`FileSage.spec`) uses onedir mode and bundles the AI packages and `webui/` assets. `launcher.py` is the entry point; `gui.py` resolves bundled assets via `sys._MEIPASS`. The GUI lazy-loads the AI stack, so startup stays fast.

## Project layout

- `organizer/` — application code (see [architecture.md](architecture.md))
- `tests/` — pytest suite
- `config.json` — default category rules
- `launcher.py` + `FileSage.spec` — PyInstaller build for the Windows exe
- `docs/` — user and architecture documentation
- `examples/` — sample configs and usage scripts

## Release process

1. Bump the version in `pyproject.toml`.
2. Update `COMMANDS.md` and the README if commands changed.
3. Ensure `python -m pytest -v` passes locally.
4. Push to `main` (CI runs the suite).
5. Tag a release and publish:

   ```bash
   git tag v0.5.0
   git push origin v0.5.0
   python -m build
   twine upload dist/*
   ```

6. Build and attach the Windows app to the release:

   ```bash
   python -m PyInstaller FileSage.spec --noconfirm
   # zip dist\FileSage and attach the zip to the GitHub release
   ```
