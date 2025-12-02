# hailo_logger.py
from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any

# ---- module state (singleton-ish) ----
_CONFIGURED = False

# Stable run id for this process (not printed by default)
_RUN_ID = (
    os.getenv("HAILO_RUN_ID")
    or datetime.utcnow().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
)

# Basic string->level map (kept small & obvious)
_LEVELS: dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _coerce_level(level: str | int | None) -> int:
    """Coerce a string/int/None into a logging level int."""
    if isinstance(level, int):
        return level
    if level is None:
        return logging.INFO
    return _LEVELS.get(str(level).upper(), logging.INFO)


def get_run_id() -> str:
    """Return the stable run id for this process.

    Not shown in log lines by default, but available for:
      * experiment tracking
      * test logs
      * debugging
    """
    return _RUN_ID


def init_logging(
    *,
    level: str | int | None = None,
    log_file: str | None = None,
    force: bool = False,
) -> None:
    """Configure the root logger exactly once (unless force=True).

    Priority for level:
      1) explicit param
      2) env HAILO_LOG_LEVEL
      3) env LOG_LEVEL
      4) INFO (default)

    If log_file is provided (or $HAILO_LOG_FILE is set),
    logs will also be written to that file.

    This is the only place that should touch handlers / root config.
    All other code just calls get_logger(name).
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    # Resolve level from param or env
    env_level = os.getenv("HAILO_LOG_LEVEL") or os.getenv("LOG_LEVEL")
    resolved_level = _coerce_level(level if level is not None else env_level)

    # Clear existing handlers to avoid duplicates (tests/notebooks/CLI reuse)
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(resolved_level)

    # Simple, standard format
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%H:%M:%S"

    # Console handler (stderr)
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    root.addHandler(ch)

    # Optional file handler
    log_file = log_file or os.getenv("HAILO_LOG_FILE")
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        root.addHandler(fh)

    # Be quiet about common noisy deps unless user explicitly wants DEBUG
    logging.getLogger("urllib3").setLevel(max(resolved_level, logging.WARNING))
    logging.getLogger("PIL").setLevel(max(resolved_level, logging.WARNING))

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Creates or retrieves a logger configured according to LOG_LEVEL from .env.
    Falls back to INFO if not specified or invalid.

    Uses a simple format: "%(levelname)s: %(message)s" for cleaner output.
    """
    # Read log level from .env, default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = valid_levels.get(log_level_str, logging.INFO)

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        # Simple format: just level and message (no timestamp, name, run_id clutter)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


def add_logging_cli_args(parser) -> None:
    """Convenience helper: add --log-level/--debug/--log-file flags to an argparse parser."""
    parser.add_argument(
        "--log-level",
        default=os.getenv("HAILO_LOG_LEVEL", "INFO"),
        choices=[k.lower() for k in _LEVELS.keys()],
        help="Logging level (default: %(default)s or $HAILO_LOG_LEVEL / $LOG_LEVEL).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Shortcut for DEBUG log level (overrides --log-level).",
    )
    parser.add_argument(
        "--log-file",
        default=os.getenv("HAILO_LOG_FILE"),
        help="Optional log file path (also respects $HAILO_LOG_FILE).",
    )


def level_from_args(args: Any) -> str:
    """Resolve level string from argparse args."""
    return (
        "DEBUG"
        if getattr(args, "debug", False)
        else str(getattr(args, "log_level", "INFO")).upper()
    )


# If someone forgets to init, default to simple INFO console logging.
if os.getenv("HAILO_LOG_AUTOCONFIG", "1") == "1":
    try:
        init_logging()
    except Exception:
        # Avoid crashing on import due to logging config issues
        pass
