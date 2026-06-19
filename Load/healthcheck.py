#!/usr/bin/env python3
"""
Health check script for Docker-based PostgreSQL and ETL staging tables.

Verifies:
1. PostgreSQL container is running and accessible
2. Database exists
3. All staging tables exist with correct columns
4. Data directory and CSV files are accessible

Usage:
    python healthcheck.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root.parent))

from etl_pipeline.db_connection import create_db_engine, test_connection, verify_database_exists, verify_staging_tables
from etl_pipeline.config import DATA_DIR, STAGING_TABLES, LOGS_DIR, REPORTS_DIR, DIAGRAMS_DIR
from etl_pipeline.logger import get_logger
import logging

logger = get_logger("healthcheck")
logger.setLevel(logging.INFO)


def check_directories() -> bool:
    """Verify that required directories exist."""
    dirs_to_check = [DATA_DIR, LOGS_DIR, REPORTS_DIR, DIAGRAMS_DIR]
    
    print("\n" + "="*80)
    print("CHECKING DIRECTORIES")
    print("="*80)
    
    for d in dirs_to_check:
        if d.exists():
            print(f"✓ {d.relative_to(project_root.parent)}")
        else:
            print(f"✗ {d.relative_to(project_root.parent)} - NOT FOUND")
            return False
    
    return True


def check_csv_files() -> bool:
    """Verify that all required CSV files exist."""
    required_csvs = [
        "etl_batch.csv",
        "contacts.csv",
        "customers.csv",
        "products.csv",
        "sales_orders.csv",
        "order_lines.csv",
    ]
    
    print("\n" + "="*80)
    print("CHECKING CSV FILES")
    print("="*80)
    
    all_found = True
    for csv_file in required_csvs:
        path = DATA_DIR / csv_file
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✓ {csv_file:30s} ({size_mb:.2f} MB)")
        else:
            print(f"✗ {csv_file:30s} - NOT FOUND")
            all_found = False
    
    return all_found


def check_database_connection() -> bool:
    """Verify database connectivity."""
    print("\n" + "="*80)
    print("CHECKING DATABASE CONNECTION")
    print("="*80)
    
    try:
        engine = create_db_engine()
        ok, msg = test_connection(engine)
        
        if ok:
            print(f"✓ {msg}")
            return True
        else:
            print(f"✗ {msg}")
            return False
    
    except Exception as exc:
        print(f"✗ Failed to create engine: {exc}")
        logger.exception("Engine creation failed")
        return False


def check_database_exists(engine) -> bool:
    """Verify target database exists."""
    print("\n" + "="*80)
    print("CHECKING DATABASE")
    print("="*80)
    
    ok, msg = verify_database_exists(engine)
    if ok:
        print(f"✓ {msg}")
        return True
    else:
        print(f"✗ {msg}")
        return False


def check_staging_tables(engine) -> bool:
    """Verify all staging tables exist."""
    print("\n" + "="*80)
    print("CHECKING STAGING TABLES")
    print("="*80)
    
    expected_tables = list(STAGING_TABLES.keys())
    ok, missing = verify_staging_tables(engine, expected_tables)
    
    if ok:
        for table in expected_tables:
            print(f"✓ {table}")
        return True
    else:
        if missing:
            print(f"✗ Missing tables:")
            for t in missing:
                print(f"  - {t}")
            print("\nRun SQL scripts to create tables:")
            print("  1. psql -U postgres -d shoporder -f etl_pipeline/database/01_create_database.sql")
            print("  2. psql -U postgres -d shoporder -f etl_pipeline/database/02_create_staging_tables.sql")
        return False


def main():
    """Run all health checks."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "ETL PRE-FLIGHT HEALTH CHECK".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    checks = []
    
    # Check directories
    checks.append(("Directories", check_directories()))
    
    # Check CSV files
    checks.append(("CSV Files", check_csv_files()))
    
    # Check database connection
    checks.append(("Database Connection", check_database_connection()))
    
    # If connection successful, check database and tables
    if checks[-1][1]:
        try:
            engine = create_db_engine()
            checks.append(("Database Exists", check_database_exists(engine)))
            checks.append(("Staging Tables", check_staging_tables(engine)))
        except Exception as exc:
            logger.exception("Failed to check database/tables")
            checks.append(("Database Exists", False))
            checks.append(("Staging Tables", False))
    
    # Print summary
    print("\n" + "="*80)
    print("HEALTH CHECK SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    
    for name, ok in checks:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{status:8s} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! ETL is ready to run.")
        print("  Execute: python -m etl_pipeline.main")
        return 0
    else:
        print("\n✗ Some checks failed. See diagnostics above.")
        print("\nCommon fixes:")
        print("  1. Start Docker MySQL: docker compose up -d")
        print("  2. Wait 10-15s for MySQL to initialize")
        print("  3. Create database/tables: mysql -u root -p < etl_pipeline/database/01_create_database.sql")
        print("  4. Re-run this script: python healthcheck.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

