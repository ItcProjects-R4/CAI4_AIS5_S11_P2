"""
Validation utilities for staging tables.

Provides functions to:
- count rows
- detect NULLs
- detect duplicate business keys
- generate simple summary statistics
- verify successful loading

The module is intentionally conservative: business keys must be configured
in `project.config.BUSINESS_KEYS` before running duplicate checks.
"""
from typing import Dict, List, Tuple, Any
import pandas as pd
from sqlalchemy.engine import Engine
from ..config import BUSINESS_KEYS


def count_rows(engine: Engine, table_name: str) -> int:
    q = f"SELECT COUNT(*) AS cnt FROM {table_name}"
    df = pd.read_sql_query(q, engine)
    return int(df["cnt"].iloc[0])


def detect_nulls(engine: Engine, table_name: str) -> Dict[str, int]:
    # Get column names
    sample = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 0", engine)
    cols = sample.columns.tolist()
    nulls = {}
    for c in cols:
        q = f"SELECT COUNT(*) AS cnt FROM {table_name} WHERE {c} IS NULL"
        df = pd.read_sql_query(q, engine)
        cnt = int(df["cnt"].iloc[0])
        if cnt > 0:
            nulls[c] = cnt
    return nulls


def detect_duplicates(engine: Engine, table_name: str, keys: List[str]) -> int:
    if not keys:
        return 0
    key_list = ", ".join(keys)
    q = (
        f"SELECT COUNT(*) AS cnt FROM ("
        f"SELECT {key_list}, COUNT(*) AS c FROM {table_name} GROUP BY {key_list} HAVING COUNT(*) > 1"
        f") dup"
    )
    df = pd.read_sql_query(q, engine)
    return int(df["cnt"].iloc[0])


def summary_statistics(engine: Engine, table_name: str, numeric_columns: List[str] = None) -> Dict[str, Dict]:
    # Basic summary using pandas for specified numeric columns.
    if numeric_columns is None:
        # fallback: sample table and infer numeric columns
        sample = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1000", engine)
        numeric_columns = sample.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_columns:
        return {}

    q = f"SELECT {', '.join(numeric_columns)} FROM {table_name}"
    df = pd.read_sql_query(q, engine)
    stats = df.describe().to_dict()
    return stats


def run_full_validation(engine: Engine, tables: List[str]) -> Dict[str, Dict]:
    results = {}
    for t in tables:
        row_count = count_rows(engine, t)
        nulls = detect_nulls(engine, t)
        keys = BUSINESS_KEYS.get(t, [])
        dup_count = detect_duplicates(engine, t, keys)
        stats = summary_statistics(engine, t)

        results[t] = {
            "rows": row_count,
            "nulls": nulls,
            "duplicate_business_keys": dup_count,
            "summary_statistics": stats,
        }

    return results


def data_quality_checks(engine: Engine, table_name: str) -> Dict[str, Dict]:
    """Run simple data-quality checks for numeric ranges and basic anomalies.

    Returns a mapping of checks to detected issue counts or samples.
    """
    issues = {}
    # Example checks depending on table
    if table_name == "stg_order_line":
        # quantity and unit_price should be non-negative
        q1 = pd.read_sql_query(f"SELECT COUNT(*) AS cnt FROM {table_name} WHERE quantity < 0", engine)
        q2 = pd.read_sql_query(f"SELECT COUNT(*) AS cnt FROM {table_name} WHERE unit_price < 0", engine)
        issues["negative_quantity"] = int(q1["cnt"].iloc[0])
        issues["negative_unit_price"] = int(q2["cnt"].iloc[0])

    if table_name == "stg_product":
        q = pd.read_sql_query(f"SELECT COUNT(*) AS cnt FROM {table_name} WHERE list_price < 0", engine)
        issues["negative_list_price"] = int(q["cnt"].iloc[0])

    if table_name == "stg_sales_order":
        q = pd.read_sql_query(f"SELECT COUNT(*) AS cnt FROM {table_name} WHERE order_total < 0", engine)
        issues["negative_order_total"] = int(q["cnt"].iloc[0])

    return issues


def verify_post_load(engine: Engine, table_name: str) -> Dict[str, Any]:
    """Run row counts, null detection, duplicates and DQ checks for a single table.

    Returns a consolidated dict of results.
    """
    keys = BUSINESS_KEYS.get(table_name, [])
    return {
        "rows": count_rows(engine, table_name),
        "nulls": detect_nulls(engine, table_name),
        "duplicates": detect_duplicates(engine, table_name, keys),
        "dq_issues": data_quality_checks(engine, table_name),
    }
