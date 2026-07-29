from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG: logging.Logger | None = None


def setup_logger(log_dir: str = "logs") -> logging.Logger:
    global _LOG

    logger = logging.getLogger("organizer")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    log_path = Path(log_dir) / "organizer.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(str(log_path), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s")
    )
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)

    _LOG = logger
    return logger


def get_logger() -> logging.Logger:
    global _LOG
    if _LOG is None:
        return setup_logger()
    return _LOG
