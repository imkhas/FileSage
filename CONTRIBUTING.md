# Contributing to OpenFileAI

Thank you for contributing! OpenFileAI is a privacy-first, local AI file assistant. The core rule of this project:

> **No user data ever leaves the device.** Any change that uploads, streams, or transmits user files or metadata to external services will be rejected.

## Getting Started

1. Fork the repository and clone it locally.
2. Install in editable mode with dev dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate       # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Run the test suite to make sure everything is green:

   ```bash
   python -m pytest -v
   ```

## Development Workflow

1. Create a branch from `main`:

   ```bash
   git checkout -b feature/your-feature
   ```

2. Make your changes.
3. Add or update tests in `tests/`. Keep tests fast — never require a model download; mock `embedder`/`vector_store` where needed.
4. Run the full test suite:

   ```bash
   python -m pytest -v
   ```

5. Open a pull request against `main`.

## Pull Request Checklist

- [ ] Tests pass locally (`python -m pytest -v`)
- [ ] New functionality has test coverage
- [ ] No user data is sent anywhere (see the privacy rule above)
- [ ] No secrets, keys, or personal paths committed
- [ ] CLI changes documented in `COMMANDS.md`
- [ ] README/docs updated if user-facing behavior changed

## Code Style

- Python 3.10+, `from __future__ import annotations` at the top of modules
- Type hints on public functions
- Match the existing style (no external formatter is enforced yet)
- No comments unless they add real value

## Reporting Issues

Include:

- The command you ran
- The full error output
- OS and Python version (`python --version`)
- Whether the issue is reproducible on a small sample folder

## Project Structure

See [docs/architecture.md](docs/architecture.md) for a module overview.
