"""
Load Module
───────────
Loads validated clean CSVs from data/clean/ into PostgreSQL staging
tables, then upserts into the gold layer.

Load order (FK dependencies):
  etl_batch → contacts → customers → products → sales_orders → order_line
"""

from __future__ import annotations

from pathlib import Path

from etl.config import (
    CLEAN_FILES,
    LOAD_ORDER,
    DB_CONFIG,
    FIELDS,
    prompt_db_config,
)
from etl.utils.db import (
    ensure_database,
    truncate_staging,
    load_csv_to_staging,
    run_upsert,
    get_table_counts,
    execute_sql_file,
)
from etl.utils.logger import get_logger

log = get_logger("load")


def load_all(
    transform_results: dict[str, dict[str, list[dict]]] | None = None,
    skip_db: bool = False,
) -> dict[str, int]:
    """
    Load pipeline:
      1. Ensure database exists
      2. Execute schema scripts
      3. Truncate staging
      4. Load data/clean/ CSVs into staging
      5. Upsert staging → gold
    """
    log.info("═" * 60)
    log.info("LOAD PHASE")
    log.info("═" * 60)

    if skip_db:
        log.info("skip_db=True — skipping database operations.")
        return {t: 0 for t in LOAD_ORDER}

    prompt_db_config()
    ensure_database()

    from etl.config import GOLD_TABLE_MAP, SQL_SCRIPTS_DIR
    schema_file = SQL_SCRIPTS_DIR / "02_create_tables.sql"
    if schema_file.exists():
        execute_sql_file(schema_file)

    truncate_staging()

    counts: dict[str, int] = {}
    for table_name in LOAD_ORDER:
        csv_path = CLEAN_FILES[table_name]
        columns = FIELDS[table_name]
        count = load_csv_to_staging(table_name, csv_path, columns)
        counts[table_name] = count

    run_upsert()

    gold_counts = get_table_counts()
    log.info("Final gold table counts:")
    for t in GOLD_TABLE_MAP.values():
        log.info("  %s: %d", t, gold_counts.get(t, -1))

    return counts
