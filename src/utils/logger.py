"""
utils/logger.py — Structured, rotating file logger + coloured console output.

Usage:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Camera opened")
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "attention_tracker.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
_BACKUP_COUNT = 3

_CONSOLE_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_FILE_FMT = "%(asctime)s [%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d) — %(message)s"
_DATE_FMT = "%H:%M:%S"

# ANSI colours for console
_COLOURS: dict[str, str] = {
    "DEBUG": "\033[36m",    # cyan
    "INFO": "\033[32m",     # green
    "WARNING": "\033[33m",  # yellow
    "ERROR": "\033[31m",    # red
    "CRITICAL": "\033[35m", # magenta
    "RESET": "\033[0m",
}


class _ColouredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        reset = _COLOURS["RESET"]
        record.levelname = f"{colour}{record.levelname}{reset}"
        return super().format(record)


def _build_root_logger() -> logging.Logger:
    root = logging.getLogger("attention_tracker")
    root.setLevel(logging.DEBUG)

    # ── Console handler ──────────────────────────────────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(_ColouredFormatter(_CONSOLE_FMT, datefmt=_DATE_FMT))
    root.addHandler(ch)

    # ── File handler ─────────────────────────────────────────────────────────
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            _LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
        root.addHandler(fh)
    except OSError:
        root.warning("Could not create log file; logging to console only.")

    return root


_root_logger = _build_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'attention_tracker' namespace."""
    return _root_logger.getChild(name)
