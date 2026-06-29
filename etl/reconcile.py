"""
Reconcile Module
────────────────
Compares pipeline output against source clean CSVs and DB counts.
"""

from __future__ import annotations

import csv
from pathlib import Path

from etl.config import SOURCE_FILES, CLEAN_FILES, RAW_FILES, QUARANTINE_FILES, REJECTED_FILES, LOAD_ORDER, STAGING_TABLE_MAP, GOLD_TABLE_MAP
from etl.utils.db import get_table_counts
from etl.utils.logger import get_logger

log = get_logger("reconcile")


class ReconciliationReport:
    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, name: str, passed: bool, expected: int = 0, actual: int = 0, detail: str = "") -> None:
        self.checks.append({"check": name, "passed": passed, "expected": expected, "actual": actual, "detail": detail})

    def summary(self) -> str:
        lines = ["══ Reconciliation Report ══"]
        for c in self.checks:
            mark = "PASS" if c["passed"] else "FAIL"
            exp = f" (expected={c['expected']}, actual={c['actual']})" if c["expected"] else ""
            lines.append(f"  [{mark}] {c['check']}{exp} — {c['detail']}")
        verdict = "ALL CHECKS PASSED" if all(c["passed"] for c in self.checks) else "SOME CHECKS FAILED"
        lines.append(f"  VERDICT: {verdict}")
        return "\n".join(lines)


def _count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)


def reconcile_all() -> ReconciliationReport:
    log.info("Running reconciliation …")
    r = ReconciliationReport()

    table_map = {"contacts", "customers", "products", "sales_orders", "order_lines"}

    for tbl in table_map:
        source_count = _count_csv(SOURCE_FILES[tbl])
        clean_count = _count_csv(CLEAN_FILES[tbl])
        raw_count = _count_csv(RAW_FILES[tbl])
        q_count = _count_csv(QUARANTINE_FILES[tbl])
        rr_count = _count_csv(REJECTED_FILES[tbl])

        # No rows lost in transform: clean + quarantine + rejected == raw
        total = clean_count + q_count + rr_count
        r.add(f"{tbl}: no rows lost (clean+q+r == raw)", total == raw_count,
              expected=raw_count, actual=total,
              detail=f"clean={clean_count} q={q_count} r={rr_count}")

    # DB counts (if available)
    try:
        gc = get_table_counts()
        for tbl in LOAD_ORDER:
            gold = GOLD_TABLE_MAP[tbl]
            stg = STAGING_TABLE_MAP[tbl]
            g, s = gc.get(gold, -1), gc.get(stg, -1)
            r.add(f"DB {gold} == staging {stg}", g == s, expected=s, actual=g)
    except Exception as exc:
        r.add("DB connectivity", False, detail=str(exc))

    log.info(r.summary())
    return r
