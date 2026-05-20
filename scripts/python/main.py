"""
main.py - Pipeline Orchestrator
================================
Entry point to run the full ETL pipeline in order.
Usage:  python scripts/python/main.py
"""

import subprocess
import sys
import os


def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    steps = [
        # ("Extract",         os.path.join(base_dir, "extract.py")),      # uncomment when needed
        ("Transform eg_crm", os.path.join(base_dir, "transform.py")),
        ("Transform ITC",    os.path.join(base_dir, "transform_itc.py")),
        # ("Load",            os.path.join(base_dir, "load.py")),          # uncomment when built
    ]

    print("=" * 50)
    print("  Pipeline Orchestrator")
    print("=" * 50 + "\n")

    for name, script in steps:
        print(f"[{name}] Running {os.path.basename(script)} ...")
        result = subprocess.run([sys.executable, script], cwd=os.getcwd())
        if result.returncode != 0:
            print(f"[{name}] FAILED (exit code {result.returncode})")
            sys.exit(result.returncode)
        print(f"[{name}] Done.\n")

    # Run audit
    audit_script = os.path.join(base_dir, "_audit.py")
    if os.path.exists(audit_script):
        print("[Audit] Running data integrity checks ...")
        result = subprocess.run([sys.executable, audit_script], cwd=os.getcwd())
        if result.returncode != 0:
            print("[Audit] WARNINGS detected.")
        print("[Audit] Done.\n")

    # Run DQ checks
    dq_script = os.path.join(base_dir, "dq_checks.py")
    if os.path.exists(dq_script):
        print("[DQ] Running data quality validation ...")
        result = subprocess.run([sys.executable, dq_script], cwd=os.getcwd())
        if result.returncode != 0:
            print("[DQ] WARNINGS detected.")
        print("[DQ] Done.\n")

    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
