"""Loader utilities: explicit mappings, robust inserts, and summaries.

Provides:
- `load_csv_to_table` high-level helper used by individual loaders
- pre-load validations
- robust insertion with chunked writes and per-row fallback to capture failed rows
"""
from pathlib import Path
import os
import time
import json
import pandas as pd
from sqlalchemy.engine import Engine
from typing import Tuple, List, Dict, Any

from ..config import LOGS_DIR


def _count_table_rows(engine: Engine, table_name: str) -> int:
    q = f"SELECT COUNT(*) AS cnt FROM {table_name}"
    df = pd.read_sql_query(q, engine)
    return int(df["cnt"].iloc[0])


def pre_load_checks(csv_path: Path, required_columns: List[str], logger) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not csv_path.exists():
        errors.append(f"File not found: {csv_path}")
        return False, errors

    if csv_path.stat().st_size == 0:
        errors.append(f"File is empty: {csv_path}")
        return False, errors

    # Read header only to validate columns
    try:
        header_df = pd.read_csv(csv_path, nrows=0)
        cols = header_df.columns.tolist()
    except Exception as exc:
        errors.append(f"Failed to read CSV header: {exc}")
        return False, errors

    missing = [c for c in required_columns if c not in cols]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    return (len(errors) == 0), errors


def insert_dataframe(engine: Engine, df: pd.DataFrame, table_name: str, logger, chunksize: int = 1000) -> Dict[str, Any]:
    """Insert DataFrame into table. Returns a summary dict with counts and failures.

    On bulk insert failure, falls back to per-row inserts to capture failing rows.
    """
    summary: Dict[str, Any] = {
        "rows_attempted": len(df),
        "rows_inserted": 0,
        "rows_failed": 0,
        "failed_row_samples": [],
    }

    if len(df) == 0:
        return summary

    start_before = _count_table_rows(engine, table_name)

    try:
        with engine.begin() as conn:
            df.to_sql(name=table_name, con=conn, if_exists="append", index=False, method="multi", chunksize=chunksize)

        end_after = _count_table_rows(engine, table_name)
        summary["rows_inserted"] = end_after - start_before
        return summary

    except Exception as bulk_exc:
        logger.warning(f"Bulk insert failed for {table_name}: {bulk_exc}. Falling back to row-wise insertion.")
        inserted = 0
        failed = 0
        samples: List[Dict[str, Any]] = []
        with engine.begin() as conn:
            for idx, row in df.iterrows():
                try:
                    row_df = pd.DataFrame([row])
                    row_df.to_sql(name=table_name, con=conn, if_exists="append", index=False)
                    inserted += 1
                except Exception as row_exc:
                    failed += 1
                    if len(samples) < 10:
                        samples.append({"index": int(idx), "error": str(row_exc), "row": row.to_dict()})

        summary["rows_inserted"] = inserted
        summary["rows_failed"] = failed
        summary["failed_row_samples"] = samples
        return summary


def load_csv_to_table(csv_path: Path, table_name: str, engine: Engine, staging_columns: List[str], logger) -> Dict[str, Any]:
    """High-level loader used by individual loader modules.

    Steps:
    - pre-load checks (exists, not empty, required columns)
    - read CSV
    - prepare DataFrame with explicit column mapping (add missing columns as None, drop extras)
    - insert via `insert_dataframe`
    - post-load validation (row counts)
    - return a detailed summary dict
    """
    t0 = time.perf_counter()
    summary: Dict[str, Any] = {"table": table_name, "csv": str(csv_path), "start_time": time.time()}

    ok, errors = pre_load_checks(csv_path, staging_columns, logger)
    if not ok:
        summary.update({"status": "precheck_failed", "errors": errors, "duration_s": time.perf_counter() - t0})
        logger.error("Pre-load checks failed: %s", errors)
        return summary

    # Row count before load
    try:
        before_count = _count_table_rows(engine, table_name)
    except Exception:
        before_count = None

    # Read CSV fully
    df = pd.read_csv(csv_path)
    rows_read = len(df)
    logger.info(f"{csv_path.name}: {rows_read} rows read")
    summary["rows_read"] = rows_read

    # Prepare DataFrame columns to match staging schema exactly
    # Add missing columns with None and keep ordering
    df_to_load = df.copy()
    # Fill missing columns
    for c in staging_columns:
        if c not in df_to_load.columns:
            df_to_load[c] = None

    # Reduce extra columns and maintain staging order
    df_to_load = df_to_load.loc[:, [c for c in staging_columns if c in df_to_load.columns]]
    
    # PostgreSQL boolean conversion
    if table_name == "stg_product" and "is_active" in df_to_load.columns:
        df_to_load["is_active"] = (
            df_to_load["is_active"]
            .fillna(0)
            .astype(int)
            .astype(bool)
        )
    # Perform insertion
    insert_summary = insert_dataframe(engine, df_to_load, table_name, logger)
    summary.update(insert_summary)

    # Post-load counts
    try:
        after_count = _count_table_rows(engine, table_name)
    except Exception:
        after_count = None

    summary.update({"before_count": before_count, "after_count": after_count})
    summary.update({"status": "loaded" if summary.get("rows_failed", 0) == 0 else "partial_failure"})
    summary.update({"duration_s": time.perf_counter() - t0})

    # Save a summary JSON file near logs for traceability
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        summary_file = LOGS_DIR / f"load_summary_{table_name}_{int(time.time())}.json"
        with open(summary_file, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, default=str, indent=2)
        logger.info(f"Wrote load summary to {summary_file}")
    except Exception as e:
        logger.warning(f"Failed to write load summary file: {e}")

    return summary
