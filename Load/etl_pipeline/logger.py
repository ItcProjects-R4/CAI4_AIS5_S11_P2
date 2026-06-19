"""
Centralized logger configuration for the ETL project.

Exports `get_logger(name)` to provide consistent logging across modules.
"""
import logging
from logging.handlers import RotatingFileHandler
from .config import LOGS_DIR


LOG_DIR = LOGS_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "etl.log"


def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    fh = RotatingFileHandler(LOG_FILE, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(logging.INFO)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
