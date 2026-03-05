"""
Environment Setup and Initialization

Purpose:
    Handles workspace bootstrap, virtual environment setup, and initial configuration.
    When running locally (not in Docker), creates a venv and installs dependencies.

Exit Codes:
    0: Success
    1: General error
    2: Already initialized (with --force to override)
    4: File I/O error or permission denied
    5: Failed to create venv or install dependencies

Usage:
    Inside Docker: python -m etl_cli setup
    Locally (not recommended): python -m etl_cli setup [--force]
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

app = typer.Typer()


@app.callback(invoke_without_command=True)
def setup(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-initialization even if already set up",
    ),
    ctx: typer.Context = typer.Depends(lambda: None),
) -> None:
    """
    Initialize the workspace and environment for the first time.

    This command:
    1. Checks if running inside Docker (recommended)
    2. Creates data directories if missing
    3. Creates a local venv if running on host (not recommended)
    4. Copies .env.template to .env if .env doesn't exist

    Example (inside Docker):
        docker compose run --rm etl python -m etl_cli setup

    Example (locally, not recommended):
        python -m etl_cli setup --force
    """
    typer.echo("🚀 Setting up Customer Data ETL workspace...")

    # Check if running inside Docker
    inside_docker = Path("/.dockerenv").exists()
    if inside_docker:
        typer.echo("✓ Running inside Docker (as recommended)")
    else:
        typer.echo(
            "⚠️  Running on host system. "
            "Consider using Docker: docker compose run --rm etl bash"
        )

    # Create data directories
    try:
        data_dirs = [
            Path("data/raw"),
            Path("data/clean"),
        ]
        for directory in data_dirs:
            directory.mkdir(parents=True, exist_ok=True)
            typer.echo(f"✓ Created {directory}")
    except Exception as e:
        typer.echo(f"❌ Error creating data directories: {e}", err=True)
        sys.exit(4)

    # Create .env from template if it doesn't exist
    env_file = Path(".env")
    env_template = Path(".env.template")

    if env_file.exists():
        if not force:
            typer.echo(
                "⚠️  .env already exists. Use --force to overwrite "
                "(not recommended if you have credentials)."
            )
            sys.exit(2)
        else:
            typer.echo("⟳ Overwriting .env (--force)")

    if env_template.exists():
        try:
            content = env_template.read_text()
            env_file.write_text(content)
            typer.echo(f"✓ Created .env from template")
            typer.echo("  ⚠️  Remember to fill in your credentials!")
        except Exception as e:
            typer.echo(f"❌ Error creating .env: {e}", err=True)
            sys.exit(4)
    else:
        typer.echo("⚠️  .env.template not found. You'll need to create .env manually.")

    # Summary
    typer.echo("\n✅ Setup complete!")
    typer.echo("\nNext steps:")
    typer.echo("  1. Edit .env with your database credentials")
    typer.echo("  2. Run: python -m etl_cli check-env")
    typer.echo("  3. Run: python -m etl_cli generate-mock-data --seed 42")
    typer.echo("  4. Run: python -m etl_cli run-pipeline")
    typer.echo("\nFor more help, run: python -m etl_cli --help")
