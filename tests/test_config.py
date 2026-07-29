from __future__ import annotations

import json
import tempfile
from pathlib import Path

from organizer.config_loader import load_config


def test_load_valid_config():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = {"Images": [".jpg", ".png"], "Docs": [".pdf"]}
        path = Path(tmp) / "config.json"
        path.write_text(json.dumps(cfg), encoding="utf-8")
        result = load_config(path)
        assert result == cfg


def test_load_missing_file_raises():
    try:
        load_config("/tmp/nonexistent_config.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_load_malformed_json_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.json"
        path.write_text("not json", encoding="utf-8")
        try:
            load_config(path)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


def test_load_invalid_structure_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.json"
        path.write_text('["not", "a", "dict"]', encoding="utf-8")
        try:
            load_config(path)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
