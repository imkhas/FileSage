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

The suite must stay fast and offline. The sentence-transformer model and FAISS are mocked in tests (`test_embedder.py`, `test_vector_store.py`, `test_search.py`) so no model download ever happens in CI.

## CI

`.github/workflows/ci.yml` runs the full test suite on push and pull requests to `main` (Python 3.11, Ubuntu).

## Project layout

- `organizer/` — application code (see [architecture.md](architecture.md))
- `tests/` — pytest suite
- `config.json` — default category rules
- `docs/` — user and architecture documentation
- `examples/` — sample configs and usage scripts

## Release process

1. Bump the version in `pyproject.toml`.
2. Update `COMMANDS.md` and the README if commands changed.
3. Ensure `python -m pytest -v` passes locally.
4. Push to `main` (CI runs the suite).
5. Tag a release and publish:

   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   python -m build
   twine upload dist/*
   ```
