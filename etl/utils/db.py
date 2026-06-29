"""
PostgreSQL database utility module.
──────────────────────────────────
Handles:
  - Creating the shopOrder database
  - Executing SQL scripts
  - Loading CSV data into staging tables
  - Running validation queries
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from etl.config import DB_CONFIG, SQL_SCRIPTS_DIR, LOAD_ORDER, STAGING_TABLE_MAP, GOLD_TABLE_MAP
from etl.utils.logger import get_logger

log = get_logger("db")


def _conn(dbname: str | None = None) -> psycopg2.extensions.connection:
    cfg = dict(DB_CONFIG)
    if dbname:
        cfg["database"] = dbname
    return psycopg2.connect(**cfg)


def ensure_database() -> None:
    """Create shopOrder database if it does not exist."""
    log.info("Ensuring database '%s' exists …", DB_CONFIG["database"])
    conn = _conn("postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_CONFIG["database"],),
    )
    if cur.fetchone() is None:
        cur.execute(f'CREATE DATABASE "{DB_CONFIG["database"]}"')
        log.info("  → database created.")
    else:
        log.info("  → database already exists.")
    cur.close()
    conn.close()


def execute_sql_file(filepath: Path, dbname: str | None = None) -> None:
    """Execute a SQL script file against the database."""
    log.info("Executing %s …", filepath.name)
    conn = _conn(dbname or DB_CONFIG["database"])
    cur = conn.cursor()
    sql = filepath.read_text(encoding="utf-8")
    try:
        cur.execute(sql)
        conn.commit()
        log.info("  → OK.")
    except Exception as exc:
        conn.rollback()
        log.error("  → FAILED: %s", exc)
        raise
    finally:
        cur.close()
        conn.close()


def execute_sql_files_in_order() -> None:
    """Run the SQL scripts in dependency order (01→05)."""
    scripts = sorted(SQL_SCRIPTS_DIR.glob("*.sql"))
    for script in scripts:
        execute_sql_file(script)


def execute_sql(sql: str, dbname: str | None = None) -> list[tuple]:
    """Execute raw SQL and return fetched rows."""
    conn = _conn(dbname or DB_CONFIG["database"])
    cur = conn.cursor()
    try:
        cur.execute(sql)
        if cur.description:
            return cur.fetchall()
        conn.commit()
        return []
    finally:
        cur.close()
        conn.close()


def truncate_staging() -> None:
    """Truncate all staging tables before a fresh load."""
    log.info("Truncating staging tables …")
    tables = list(STAGING_TABLE_MAP.values())
    conn = _conn()
    cur = conn.cursor()
    for t in tables:
        cur.execute(f"TRUNCATE TABLE {t} CASCADE")
    conn.commit()
    cur.close()
    conn.close()
    log.info("  → staging tables truncated.")


def load_csv_to_staging(
    table_name: str,
    csv_path: Path,
    columns: list[str],
    batch_id: str | None = None,
) -> int:
    """
    Bulk-load a CSV file into a staging table using COPY.
    Returns the number of rows loaded.
    """
    staging_table = STAGING_TABLE_MAP[table_name]
    log.info("Loading %s → %s …", csv_path.name, staging_table)
    if not csv_path.exists():
        log.warning("  → file not found, skipping.")
        return 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        log.warning("  → empty file, skipping.")
        return 0
    col_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {staging_table} ({col_list}) VALUES ({placeholders})"

    conn = _conn()
    cur = conn.cursor()
    count = 0
    for row in rows:
        values = [row.get(c, None) or None for c in columns]
        try:
            cur.execute(insert_sql, values)
            count += 1
        except Exception as exc:
            conn.rollback()
            log.error("  → row %d failed: %s", count + 1, exc)
            raise
    conn.commit()
    cur.close()
    conn.close()
    log.info("  → %d rows loaded into %s.", count, staging_table)
    return count


def run_upsert() -> None:
    """Execute the staging → gold upsert procedure."""
    log.info("Running staging → gold upsert …")
    execute_sql_file(SQL_SCRIPTS_DIR / "04_load_procedures.sql")
    log.info("  → upsert complete.")


def run_validation() -> list[tuple]:
    """Execute the validation queries and return results."""
    log.info("Running validation queries …")
    results = execute_sql_file_returning(
        SQL_SCRIPTS_DIR / "05_validation_queries.sql"
    )
    return results


def execute_sql_file_returning(filepath: Path) -> list[tuple]:
    """Execute a SQL file and return any result sets."""
    conn = _conn()
    cur = conn.cursor()
    sql = filepath.read_text(encoding="utf-8")
    try:
        cur.execute(sql)
        if cur.description:
            return cur.fetchall()
        conn.commit()
        return []
    finally:
        cur.close()
        conn.close()


def get_table_counts() -> dict[str, int]:
    """Return row counts for gold + staging tables."""
    tables = list(GOLD_TABLE_MAP.values()) + list(STAGING_TABLE_MAP.values())
    counts = {}
    conn = _conn()
    cur = conn.cursor()
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
        except Exception:
            counts[t] = -1
    cur.close()
    conn.close()
    return counts
