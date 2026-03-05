"""
Environment Diagnostics and Validation

Purpose:
    Diagnoses the runtime environment: checks for required Python packages,
    database drivers, environment variables, and connectivity.
    Provides clear error messages and remediation steps.

Exit Codes:
    0: OK - all checks passed
    1: General error
    2: Missing .env file or required configuration
    3: Missing required package or driver
    4: File read error
    5: Database connection failed

Usage:
    python -m etl_cli check-env
    docker compose run --rm etl python -m etl_cli check-env
"""

import sys
from pathlib import Path

try:
    import typer
    from dotenv import load_dotenv
except ImportError as e:
    print(
        f"Error: Required package not found: {e}",
        file=sys.stderr,
    )
    sys.exit(3)

import os

app = typer.Typer()


def check_python_version() -> bool:
    """Check Python version is 3.10 or later."""
    if sys.version_info < (3, 10):
        typer.echo(
            f"❌ Python 3.10+ required, got {sys.version_info.major}.{sys.version_info.minor}",
            err=True,
        )
        return False
    typer.echo(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_required_packages() -> bool:
    """Check for required Python packages."""
    required = ["typer", "dotenv", "pandas", "openpyxl"]
    optional = ["pyodbc"]
    missing = []

    for package_name in required:
        try:
            __import__(package_name.replace("-", "_"))
            typer.echo(f"✓ {package_name} installed")
        except ImportError:
            typer.echo(f"❌ {package_name} NOT installed", err=True)
            missing.append(package_name)

    typer.echo("")
    for package_name in optional:
        try:
            __import__(package_name.replace("-", "_"))
            typer.echo(f"✓ {package_name} (optional) installed")
        except ImportError:
            typer.echo(f"⚠️  {package_name} (optional) NOT installed")

    if missing:
        typer.echo(f"\n❌ Missing {len(missing)} required package(s)", err=True)
        return False

    return True


def check_odbc_drivers() -> bool:
    """Check available ODBC drivers."""
    try:
        import pyodbc

        drivers = pyodbc.drivers()
        typer.echo(f"\nODBC Drivers ({len(drivers)} found):")
        if drivers:
            for driver in drivers:
                typer.echo(f"  ✓ {driver}")
            return True
        else:
            typer.echo("  ⚠️  No ODBC drivers installed")
            typer.echo(
                "  This is OK for development. For production, install msodbcsql18."
            )
            return True
    except ImportError:
        typer.echo("\n⚠️  pyodbc not installed. Install to check ODBC drivers.")
        return True
    except Exception as e:
        typer.echo(f"\n⚠️  Could not check ODBC drivers: {e}")
        return True


def check_environment_variables() -> bool:
    """Check for required environment variables."""
    # Load .env if exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(".env")
        typer.echo("✓ .env file loaded")
    else:
        typer.echo("⚠️  .env file not found. Run: cp .env.template .env")

    # Check required variables
    required_vars = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    optional_vars = ["ENVIRONMENT", "LOG_LEVEL"]

    typer.echo("\nRequired environment variables:")
    all_present = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            masked = value[:3] + "*" * (len(value) - 6) if len(value) > 6 else "***"
            typer.echo(f"  ✓ {var}={masked}")
        else:
            typer.echo(f"  ❌ {var} NOT SET", err=True)
            all_present = False

    typer.echo("\nOptional environment variables:")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            typer.echo(f"  ✓ {var}={value}")
        else:
            typer.echo(f"  - {var} (not set, using default)")

    return all_present


def check_database_connectivity() -> bool:
    """Check database connectivity (requires credentials)."""
    try:
        import pyodbc
    except ImportError:
        typer.echo("\n⚠️  pyodbc not available. Skipping database check.")
        return True

    db_server = os.environ.get("DB_SERVER")
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")

    if not all([db_server, db_name, db_user, db_password]):
        typer.echo("\n⚠️  Database credentials not fully configured. Skipping connectivity check.")
        return True

    try:
        typer.echo("\nAttempting database connection...")
        # Build connection string (SQL Server specific)
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={db_server};DATABASE={db_name};UID={db_user};PWD={db_password}"
        )
        conn = pyodbc.connect(conn_str, timeout=5)
        conn.close()
        typer.echo("✓ Database connection successful")
        return True
    except pyodbc.Error as e:
        typer.echo(f"❌ Database connection failed: {e}", err=True)
        typer.echo(
            "  Hint: Check DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD in .env",
            err=True,
        )
        return False
    except Exception as e:
        typer.echo(f"⚠️  Could not test connection: {e}")
        return True


@app.callback(invoke_without_command=True)
def check_env(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
    check_db: bool = typer.Option(
        True, "--skip-db", help="Skip database connectivity check"
    ),
) -> None:
    """
    Diagnose the runtime environment.

    Checks:
    - Python version (3.10+)
    - Required packages (typer, pandas, openpyxl, python-dotenv)
    - Optional packages (pyodbc)
    - ODBC drivers (for SQL Server)
    - Environment variables (.env)
    - Database connectivity (optional)

    Exit code is 0 if all critical checks pass, > 0 otherwise.

    Example:
        docker compose run --rm etl python -m etl_cli check-env
        docker compose run --rm etl python -m etl_cli check-env --verbose
    """
    typer.echo("🔍 Checking environment...\n")

    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("ODBC Drivers", check_odbc_drivers),
        ("Environment Variables", check_environment_variables),
    ]

    if check_db:
        checks.append(("Database Connectivity", check_database_connectivity))

    failed = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                failed.append(check_name)
        except Exception as e:
            if verbose:
                typer.echo(f"❌ Unexpected error in {check_name}: {e}", err=True)
            failed.append(check_name)

    # Summary
    typer.echo("\n" + "=" * 60)
    if not failed:
        typer.echo("✅ All checks passed! Environment is ready.")
        sys.exit(0)
    else:
        typer.echo(f"❌ {len(failed)} check(s) failed:", err=True)
        for check_name in failed:
            typer.echo(f"  - {check_name}", err=True)
        sys.exit(1)
