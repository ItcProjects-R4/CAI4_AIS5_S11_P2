"""
ETL Pipeline Orchestrator
─────────────────────────
Reads data/raw/ → Transform → Validate → Load to DB → Reconcile.

Usage:
    python -m etl              # full pipeline (requires PostgreSQL)
    python -m etl --skip-db    # CSV-only (no DB)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.extract import extract_all
from etl.transform import transform_all
from etl.validate import validate_all
from etl.load import load_all
from etl.reconcile import reconcile_all
from etl.utils.logger import get_logger

RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
log = get_logger("main", RUN_TS)


def run_pipeline(skip_db: bool = False) -> dict:
    start = time.time()
    summary: dict = {
        "run_timestamp": RUN_TS,
        "started_at": datetime.now().isoformat(),
        "stages": {},
    }

    log.info("═" * 60)
    log.info("  ETL PIPELINE — RUN %s", RUN_TS)
    log.info("═" * 60)

    # Stage 1: Extract from data/raw/
    log.info("\n▶ STAGE 1: EXTRACT")
    t = time.time()
    raw_data = extract_all()
    summary["stages"]["extract"] = {"duration_s": round(time.time() - t, 2),
                                     "row_counts": {k: len(v) for k, v in raw_data.items()}}

    # Stage 2: Transform → data/clean/, data/quarantine/, data/rejected/
    log.info("\n▶ STAGE 2: TRANSFORM")
    t = time.time()
    transform_results = transform_all(raw_data)
    summary["stages"]["transform"] = {
        "duration_s": round(time.time() - t, 2),
        "counts": {tbl: {"clean": len(d["clean"]), "quarantine": len(d["quarantine"]),
                          "rejected": len(d["rejected"])} for tbl, d in transform_results.items()},
    }

    # Stage 3: Validate
    log.info("\n▶ STAGE 3: VALIDATE")
    t = time.time()
    validation = validate_all(transform_results)
    summary["stages"]["validate"] = {"duration_s": round(time.time() - t, 2),
                                      "passed": validation.passed,
                                      "checks": validation.checks}

    # Stage 4: Load to PostgreSQL
    log.info("\n▶ STAGE 4: LOAD")
    t = time.time()
    load_counts = load_all(transform_results, skip_db=skip_db)
    summary["stages"]["load"] = {"duration_s": round(time.time() - t, 2),
                                  "loaded_counts": load_counts}

    # Stage 5: Reconcile
    log.info("\n▶ STAGE 5: RECONCILE")
    t = time.time()
    recon = reconcile_all()
    summary["stages"]["reconcile"] = {"duration_s": round(time.time() - t, 2),
                                       "checks": recon.checks,
                                       "passed": all(c["passed"] for c in recon.checks)}

    total = time.time() - start
    summary["total_duration_s"] = round(total, 2)
    summary["completed_at"] = datetime.now().isoformat()
    summary["status"] = "completed"

    # Write summary
    from etl.config import LOG_DIR
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = LOG_DIR / f"pipeline_summary_{RUN_TS}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    log.info("\n═" * 60)
    log.info("  PIPELINE COMPLETE in %.2fs", total)
    log.info("  Summary: %s", summary_path)
    log.info("═" * 60)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL Pipeline")
    parser.add_argument("--skip-db", action="store_true", help="Skip database operations")
    args = parser.parse_args()

    try:
        summary = run_pipeline(skip_db=args.skip_db)
        sys.exit(0 if summary.get("status") == "completed" else 1)
    except Exception as exc:
        log.error("Pipeline failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
