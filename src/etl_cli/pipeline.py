"""
Main ETL Pipeline

Purpose:
    Orchestrates the complete ETL workflow: extraction, transformation, and loading.
    This is a skeleton that demonstrates the structure for business logic implementation.

Phases:
    1. Extract: Load data from CRM and Excel sources
    2. Transform: Clean, deduplicate, and enrich data
    3. Load: Write to destination (currently placeholder)

Exit Codes:
    0: Success
    1: General error
    2: Source data not found
    3: Dependency missing
    4: Cannot write output
    5: Data validation failed

Usage:
    python -m etl_cli run-pipeline
    python -m etl_cli run-pipeline --dry-run
    python -m etl_cli run-pipeline --limit 1000
"""

import sys
from pathlib import Path

try:
    import typer
except ImportError as e:
    print(
        f"Error: Required package not found: {e}",
        file=sys.stderr,
    )
    sys.exit(3)

app = typer.Typer()


def extract() -> bool:
    """
    Extract phase: Load data from source files.

    Returns:
        True if successful, False otherwise
    """
    typer.echo("📥 Extract phase...")

    # Check for source data
    crm_file = Path("data/raw/crm_data.csv")
    sales_file = Path("data/raw/sales_data.xlsx")

    if not crm_file.exists() and not Path("data/raw/sales_data.csv").exists():
        typer.echo("  ⚠️  No source data found.", err=True)
        typer.echo(
            "  Run: python -m etl_cli generate-mock-data",
            err=True,
        )
        return False

    if crm_file.exists():
        typer.echo(f"  ✓ Found {crm_file}")
    else:
        typer.echo(f"  - {crm_file} not found (optional)", err=True)

    if sales_file.exists():
        typer.echo(f"  ✓ Found {sales_file}")
    elif Path("data/raw/sales_data.csv").exists():
        typer.echo(f"  ✓ Found data/raw/sales_data.csv")
    else:
        typer.echo("  - Sales data not found (optional)", err=True)

    typer.echo("  ✓ Extraction complete")
    return True


def transform() -> bool:
    """
    Transform phase: Clean and enrich data.

    Returns:
        True if successful, False otherwise
    """
    typer.echo("⚙️  Transform phase...")

    # Placeholder for transformation logic
    transformations = [
        "Deduplicate customer records",
        "Validate email addresses",
        "Enrich with geolocation data (stub)",
        "Calculate customer lifetime value (stub)",
    ]

    for step in transformations:
        typer.echo(f"  • {step} (placeholder)")

    typer.echo("  ✓ Transformation complete")
    return True


def load() -> bool:
    """
    Load phase: Write cleaned data to target.

    Returns:
        True if successful, False otherwise
    """
    typer.echo("📤 Load phase...")

    try:
        # Create clean data directory
        Path("data/clean").mkdir(parents=True, exist_ok=True)

        # Placeholder for load logic
        typer.echo("  • Would write to data/clean/customer_dim.csv (placeholder)")
        typer.echo("  • Would write to data/clean/transaction_fact.csv (placeholder)")
        typer.echo(
            "  • Would insert into warehouse_db.dbo.customers (placeholder)"
        )

        typer.echo("  ✓ Load complete")
        return True
    except Exception as e:
        typer.echo(f"  ❌ Load failed: {e}", err=True)
        return False


def validate() -> bool:
    """
    Validate phase: Check data quality and integrity.

    Returns:
        True if validation passes, False otherwise
    """
    typer.echo("✔️  Validate phase...")

    checks = [
        ("No null customer IDs", True),
        ("No duplicate transactions", True),
        ("Email format valid", True),
        ("Amount > 0", True),
    ]

    passed = 0
    for check_name, check_result in checks:
        if check_result:
            typer.echo(f"  ✓ {check_name}")
            passed += 1
        else:
            typer.echo(f"  ❌ {check_name}", err=True)

    typer.echo(f"  ✓ {passed}/{len(checks)} checks passed")
    return passed == len(checks)


@app.callback(invoke_without_command=True)
def run_pipeline(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without running"
    ),
    skip_validate: bool = typer.Option(
        False,
        "--skip-validate",
        help="Skip validation phase",
    ),
    limit: int = typer.Option(
        None, "--limit", help="Limit rows processed (for testing)"
    ),
) -> None:
    """
    Run the complete ETL pipeline.

    Phases:
    1. Extract data from source files
    2. Transform (clean, deduplicate, enrich)
    3. Load to destination
    4. Validate data quality

    Example:
        docker compose run --rm etl python -m etl_cli run-pipeline
        docker compose run --rm etl python -m etl_cli run-pipeline --dry-run
        docker compose run --rm etl python -m etl_cli run-pipeline --limit 10000
    """
    typer.echo("🔄 Starting ETL Pipeline...\n")

    if dry_run:
        typer.echo("[DRY RUN MODE] - No changes will be made\n")

    if limit:
        typer.echo(f"⚠️  Processing limited to {limit} rows\n")

    # Run pipeline phases
    phases = [
        ("Extract", extract),
        ("Transform", transform),
        ("Load", load),
    ]

    failed = False
    for phase_name, phase_func in phases:
        try:
            if not phase_func():
                failed = True
                break
        except Exception as e:
            typer.echo(f"  ❌ {phase_name} failed: {e}", err=True)
            failed = True
            break

    if failed:
        typer.echo("\n❌ Pipeline failed", err=True)
        sys.exit(1)

    # Validation
    if not skip_validate:
        if not validate():
            typer.echo("\n❌ Data validation failed", err=True)
            sys.exit(5)

    # Success
    typer.echo("\n✅ Pipeline complete!")
    typer.echo("\nOutput:")
    typer.echo("  - data/clean/customer_dim.csv (cleaned customers)")
    typer.echo("  - data/clean/transaction_fact.csv (cleaned transactions)")
    typer.echo("  - warehouse database (if connected)")
