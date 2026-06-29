"""
Extract Module
──────────────
Reads raw CSV files from data/raw/ and returns them as in-memory data.
"""

from __future__ import annotations

import csv
from pathlib import Path

from etl.config import RAW_FILES
from etl.utils.logger import get_logger

log = get_logger("extract")


def extract_table(table_name: str) -> list[dict]:
    csv_path = RAW_FILES.get(table_name)
    if csv_path is None:
        raise ValueError(f"Unknown table: {table_name}")
    if not csv_path.exists():
        log.warning("Raw file not found: %s — returning empty list.", csv_path)
        return []

    log.info("Extracting %s …", csv_path.name)
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    log.info("  → %d rows extracted.", len(rows))
    return rows


def extract_all() -> dict[str, list[dict]]:
    log.info("Extracting all raw tables …")
    data: dict[str, list[dict]] = {}
    for name in RAW_FILES:
        data[name] = extract_table(name)
    log.info("Extraction complete: %s", {k: len(v) for k, v in data.items()})
    return data
