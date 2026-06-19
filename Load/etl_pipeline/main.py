"""
ETL Orchestration script with pre-flight checks and Docker support.

Executes loaders in the following order:

PRE-FLIGHT CHECKS
  1. Verify Docker MySQL connectivity
  2. Verify database exists
  3. Verify staging tables exist
  4. Verify required CSV files exist

ETL PIPELINE
  1. ETL_BATCH
  2. CONTACTS
  3. CUSTOMERS
  4. PRODUCTS
  5. SALES_ORDERS
  6. ORDER_LINES
  7. VALIDATION & VERIFICATION

Each loader runs in its own transaction; on failure the transaction is rolled back.
"""
from importlib import import_module
from typing import List, Dict, Any
from pathlib import Path
import json

from .db_connection import create_db_engine, test_connection, verify_database_exists, verify_staging_tables
from .logger import get_logger
from .config import DATA_DIR, STAGING_TABLES, RETRY_MAX_ATTEMPTS, RETRY_WAIT_SECONDS, LOGS_DIR, DIAGRAMS_DIR
from .validation.validation import run_full_validation, verify_post_load


logger = get_logger("etl_main")


LOADERS = [
    "etl_pipeline.loaders.load_etl_batch",
    "etl_pipeline.loaders.load_contacts",
    "etl_pipeline.loaders.load_customers",
    "etl_pipeline.loaders.load_products",
    "etl_pipeline.loaders.load_sales_orders",
    "etl_pipeline.loaders.load_order_lines",
]

REQUIRED_CSV_FILES = [
    "etl_batch.csv",
    "contacts.csv",
    "customers.csv",
    "products.csv",
    "sales_orders.csv",
    "order_lines.csv",
]


def preflight_checks(engine) -> bool:
    """Run comprehensive pre-flight validations before ETL execution.
    
    Verifies:
    - Database connectivity (with retries)
    - Database existence
    - Staging tables exist
    - Required CSV files exist
    
    Args:
        engine: SQLAlchemy Engine
    
    Returns:
        True if all checks pass, False otherwise
    """
    print("\n" + "="*80)
    print("PRE-FLIGHT CHECKS")
    print("="*80)
    
    # Check 1: Database connectivity
    print("\n1. Testing database connectivity...")
    ok, msg = test_connection(engine, RETRY_MAX_ATTEMPTS, RETRY_WAIT_SECONDS)
    if not ok:
        print(f"   ✗ FAILED: {msg}")
        logger.error(f"Database connectivity check failed: {msg}")
        return False
    print(f"   ✓ {msg}")
    logger.info("Database connectivity check passed")
    
    # Check 2: Database exists
    print("\n2. Verifying database exists...")
    ok, msg = verify_database_exists(engine)
    if not ok:
        print(f"   ✗ FAILED: {msg}")
        logger.error(f"Database existence check failed: {msg}")
        print("   Execute: python healthcheck.py")
        return False
    print(f"   ✓ {msg}")
    logger.info("Database existence check passed")
    
    # Check 3: Staging tables exist
    print("\n3. Verifying staging tables...")
    expected_tables = list(STAGING_TABLES.keys())
    ok, missing = verify_staging_tables(engine, expected_tables)
    if not ok:
        print(f"   ✗ FAILED: Missing tables: {missing}")
        logger.error(f"Staging tables check failed: {missing}")
        print("   Execute: mysql -u root -p < etl_pipeline/database/02_create_staging_tables.sql")
        return False
    for table in expected_tables:
        print(f"   ✓ {table}")
    logger.info(f"All {len(expected_tables)} staging tables verified")
    
    # Check 4: CSV files exist
    print("\n4. Verifying CSV files exist...")
    missing_csvs = []
    for csv_file in REQUIRED_CSV_FILES:
        path = DATA_DIR / csv_file
        if path.exists():
            print(f"   ✓ {csv_file}")
        else:
            print(f"   ✗ {csv_file} - NOT FOUND")
            missing_csvs.append(csv_file)
    
    if missing_csvs:
        logger.error(f"Missing CSV files: {missing_csvs}")
        return False
    logger.info(f"All {len(REQUIRED_CSV_FILES)} CSV files verified")
    
    print("\n✓ All pre-flight checks passed\n")
    return True


def run_loaders(engine) -> Dict[str, Any]:
    """Execute all loaders sequentially.
    
    Each loader returns a summary dict with row counts, failures, and timing info.
    
    Args:
        engine: SQLAlchemy Engine
    
    Returns:
        Dict mapping loader paths to their summary dicts
    """
    summaries: Dict[str, Any] = {}
    for loader_path in LOADERS:
        loader_name = loader_path.split(".")[-1]
        logger.info(f"Starting loader: {loader_name}")
        print(f"\nLoading {loader_name}...")
        
        try:
            module = import_module(loader_path)
            res = module.run()
            
            if not isinstance(res, dict):
                logger.error(f"Loader {loader_name} did not return a summary dict")
                print(f"✗ {loader_name} returned invalid result")
                return {"status": "failed", "reason": "invalid_loader_return"}
            
            summaries[loader_path] = res
            
            # Print summary for this loader
            rows_read = res.get("rows_read", 0)
            rows_inserted = res.get("rows_inserted", 0)
            rows_failed = res.get("rows_failed", 0)
            duration = res.get("duration_s", 0)
            
            print(f"✓ {loader_name}: {rows_read} read, {rows_inserted} inserted, {rows_failed} failed ({duration:.2f}s)")
            
            if rows_failed > 0:
                logger.warning(f"{loader_name} completed with {rows_failed} failed rows")
        
        except Exception as exc:
            logger.exception(f"Unhandled exception in loader {loader_name}: {exc}")
            print(f"✗ {loader_name} failed with exception: {exc}")
            return {"status": "failed", "reason": str(exc)}

    # Write combined summary
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        out = LOGS_DIR / "etl_run_summary.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(summaries, fh, default=str, indent=2)
        logger.info(f"Wrote ETL run summary to {out}")
        print(f"\nETL run summary saved to {out.relative_to(Path.cwd())}")
    except Exception as exc:
        logger.exception(f"Failed to write ETL run summary file: {exc}")

    return summaries


def run_validation(engine):
    """Run post-load data quality validations.
    
    Args:
        engine: SQLAlchemy Engine
    
    Returns:
        Validation results dict
    """
    tables = [
        "stg_etl_batch",
        "stg_contact",
        "stg_customer",
        "stg_product",
        "stg_sales_order",
        "stg_order_line",
    ]
    logger.info("Starting validation")
    print("\n" + "="*80)
    print("DATA QUALITY VALIDATION")
    print("="*80)
    
    results = run_full_validation(engine, tables)
    
    print("\nValidation Summary:")
    for t, res in results.items():
        row_count = res.get("rows", 0)
        nulls = len(res.get("nulls", {}))
        dups = res.get("duplicate_business_keys", 0)
        print(f"  {t:20s}: {row_count:8d} rows | {nulls:2d} null columns | {dups:3d} duplicates")
    
    logger.info("Validation completed")
    return results


def generate_flow_diagram():
    """Generate ETL flow diagram in Mermaid format."""
    diagram = """```mermaid
flowchart TD
    Start([START]) --> Check{Pre-Flight<br/>Checks OK?}
    Check -->|No| Failed[FAILED]
    Check -->|Yes| ETL_BATCH[Load ETL_BATCH]
    ETL_BATCH --> Contacts[Load CONTACTS]
    Contacts --> Customers[Load CUSTOMERS]
    Customers --> Products[Load PRODUCTS]
    Products --> Sales[Load SALES_ORDERS]
    Sales --> Lines[Load ORDER_LINES]
    Lines --> Validate[Validate & Verify]
    Validate --> Success[COMPLETED]
    Success --> End([END])
    Failed --> End
```
"""
    
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    path = DIAGRAMS_DIR / "etl_flow_diagram.md"
    path.write_text(diagram)
    logger.info(f"Wrote ETL flow diagram to {path}")
    print(f"ETL flow diagram saved to {path.relative_to(Path.cwd())}")


def main():
    """Main ETL orchestration function."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "ETL PIPELINE - SHOPORDER DATABASE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    logger.info("="*80)
    logger.info("ETL EXECUTION STARTED")
    logger.info("="*80)
    
    # Create engine
    try:
        engine = create_db_engine()
    except Exception as exc:
        logger.exception(f"Failed to create database engine: {exc}")
        print(f"\n✗ Failed to create database engine: {exc}")
        print("\nTroubleshooting:")
        print("  1. Ensure Docker is running: docker ps")
        print("  2. Start MySQL: docker compose up -d")
        print("  3. Wait 15 seconds for initialization")
        print("  4. Re-run this script")
        return
    
    # Run pre-flight checks
    if not preflight_checks(engine):
        print("\n✗ PRE-FLIGHT CHECKS FAILED")
        logger.error("Pre-flight checks failed")
        print("\nTroubleshooting:")
        print("  1. Run health check: python healthcheck.py")
        print("  2. Ensure Docker MySQL is running: docker compose up -d")
        print("  3. Verify tables exist: mysql -u root -p < etl_pipeline/database/02_create_staging_tables.sql")
        return
    
    # Run ETL loaders
    print("\n" + "="*80)
    print("ETL PIPELINE EXECUTION")
    print("="*80)
    
    loader_summaries = run_loaders(engine)
    
    if isinstance(loader_summaries, dict) and loader_summaries.get("status") == "failed":
        logger.error("ETL failed during loaders")
        print("\n✗ ETL FAILED DURING LOADING")
        print("\nReview logs:")
        print("  - etl_pipeline/execution_logs/etl.log (main execution log)")
        print("  - etl_pipeline/execution_logs/etl_run_summary.json (detailed row counts)")
        return
    
    # Run post-load verification
    print("\n" + "="*80)
    print("POST-LOAD VERIFICATION")
    print("="*80)
    
    verification = {}
    for table in [
        "stg_etl_batch",
        "stg_contact",
        "stg_customer",
        "stg_product",
        "stg_sales_order",
        "stg_order_line",
    ]:
        try:
            verification[table] = verify_post_load(engine, table)
        except Exception as exc:
            logger.exception(f"Verification failed for {table}: {exc}")
            verification[table] = {"error": str(exc)}
    
    # Save verification report
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        out = LOGS_DIR / "etl_verification.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(verification, fh, default=str, indent=2)
        logger.info(f"Wrote ETL verification report to {out}")
        print(f"Verification report saved to {out.relative_to(Path.cwd())}")
    except Exception as exc:
        logger.exception(f"Failed to write verification report: {exc}")
    
    # Run full validation
    validation_results = run_validation(engine)
    
    # Generate flow diagram
    generate_flow_diagram()
    
    # Print completion summary
    print("\n" + "="*80)
    print("ETL EXECUTION COMPLETED")
    print("="*80)
    print("\nOutput files:")
    print("  - etl_pipeline/execution_logs/etl.log")
    print("  - etl_pipeline/execution_logs/etl_run_summary.json")
    print("  - etl_pipeline/execution_logs/etl_verification.json")
    print("  - etl_pipeline/architecture/etl_flow_diagram.md")
    print("\nNext steps:")
    print("  1. Review logs: cat etl_pipeline/execution_logs/etl.log")
    print("  2. Check verification: cat etl_pipeline/execution_logs/etl_verification.json")
    print("  3. Query database: mysql -u root -p shopOrder")
    print("\nTo stop Docker MySQL: docker compose down")
    print()
    
    logger.info("="*80)
    logger.info("ETL EXECUTION COMPLETED")
    logger.info("="*80)


if __name__ == "__main__":
    main()
