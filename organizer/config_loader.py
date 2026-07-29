from __future__ import annotations

import json
from pathlib import Path


def load_config(config_path: str | Path) -> dict[str, list[str]]:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Config path is not a file: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}") from e

    if not isinstance(raw, dict):
        raise ValueError(
            f"Config must be a JSON object (dict), got {type(raw).__name__}"
        )

    result: dict[str, list[str]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"Category name must be a non-empty string, got {key!r}")
        if not isinstance(value, list) or not all(
            isinstance(ext, str) for ext in value
        ):
            raise ValueError(
                f"Extensions for '{key}' must be a list of strings, got {value!r}"
            )
        normalized = []
        for ext in value:
            ext = ext.strip().lower()
            if not ext.startswith("."):
                ext = "." + ext
            normalized.append(ext)
        result[key.strip()] = normalized

    return result
