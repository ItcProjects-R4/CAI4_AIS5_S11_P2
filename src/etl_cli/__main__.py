#!/usr/bin/env python3
"""
Customer Data ETL Command-Line Interface (CLI)

Purpose:
    Main entry point for the ETL pipeline. Provides Typer-based commands for
    environment setup, diagnostics, mock data generation, and pipeline execution.

Usage:
    python -m etl_cli --help
    python -m etl_cli setup
    python -m etl_cli check-env
    python -m etl_cli generate-mock-data --rows 100 --seed 42
    python -m etl_cli run-pipeline
    python -m etl_cli clean

Exit Codes:
    0: Success
    1: General error / invalid argument
    2: Environment not configured (missing .env or invalid credentials)
    3: Dependency not installed or missing system dependency
    4: File I/O error (permission, path not found, etc.)
    5: Database connection error

License: MIT
Author: Customer Data ETL Team
"""

import sys
from pathlib import Path

try:
    import typer
except ImportError:
    print(
        "Error: typer is not installed. "
        "Install with: pip install typer[all]",
        file=sys.stderr,
    )
    sys.exit(3)

from etl_cli.check_env import app as check_env_app
from etl_cli.generate_mock_data import app as generate_mock_app
from etl_cli.pipeline import app as pipeline_app
from etl_cli.setup import app as setup_app

# Create the main Typer app
app = typer.Typer(
    name="etl-cli",
    help="Customer Data ETL - Integrate, clean, and transform customer data.",
)

# Register sub-apps
app.add_typer(setup_app, name="setup", help="Initialize workspace and environment")
app.add_typer(
    check_env_app, name="check-env", help="Check environment and dependencies"
)
app.add_typer(
    generate_mock_app, name="generate-mock-data", help="Generate mock customer data"
)
app.add_typer(pipeline_app, name="run-pipeline", help="Execute the ETL pipeline")


@app.command()
def clean() -> None:
    """
    Clean up generated artifacts (data files, logs, caches).

    Exit Codes:
        0: Success
        1: Error during cleanup
    """
    typer.echo("🧹 Cleaning up generated artifacts...")

    try:
        data_files = [
            Path("data/raw/crm_data.csv"),
            Path("data/raw/sales_data.xlsx"),
        ]

        removed_count = 0
        for file in data_files:
            if file.exists():
                file.unlink()
                typer.echo(f"  ✓ Removed {file}")
                removed_count += 1

        typer.echo(f"\n✅ Cleanup complete ({removed_count} files removed).")

    except Exception as e:
        typer.echo(
            f"❌ Error during cleanup: {e}",
            err=True,
        )
        sys.exit(1)


@app.callback()
def main(ctx: typer.Context) -> None:
    """
    Customer Data ETL - Main entry point.

    Provides commands for setting up the environment, checking dependencies,
    generating test data, and running the ETL pipeline.
    """
    # Version info available via --version
    pass


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()
