"""
Logging utility — creates a timestamped logger per run.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from etl.config import LOG_DIR


def get_logger(name: str, run_ts: str | None = None) -> logging.Logger:
    """Return a configured logger writing to logs/<run_ts>/<name>.log."""
    if run_ts is None:
        run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_dir = LOG_DIR / run_ts
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"etl.{name}.{run_ts}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_dir / f"{name}.log", mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
