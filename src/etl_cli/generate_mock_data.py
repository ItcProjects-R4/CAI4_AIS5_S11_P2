"""
Mock Data Generation for Testing

Purpose:
    Generates deterministic, reproducible mock customer data for development
    and testing. Creates CRM data (CSV) and Sales data (XLSX) files with
    realistic structure and relationships.

Features:
    - Seed-based random generation for reproducibility
    - CSV output: data/raw/crm_data.csv
    - XLSX output: data/raw/sales_data.xlsx
    - Configurable row count
    - Realistic customer and transaction data

Exit Codes:
    0: Success
    1: General error
    3: Missing required dependency (pandas, openpyxl)
    4: Cannot write to output directory

Usage:
    python -m etl_cli generate-mock-data --rows 100 --seed 42
    python -m etl_cli generate-mock-data --rows 1000 --seed 12345
    python -m etl_cli generate-mock-data --no-xlsx  # Skip Excel export
"""

import sys
from pathlib import Path

try:
    import typer
import pandas as pd
except ImportError as e:
    print(
        f"Error: Required package not found: {e}",
        file=sys.stderr,
    )
    sys.exit(3)

app = typer.Typer()


def generate_crm_data(num_rows: int, seed: int) -> pd.DataFrame:
    """
    Generate mock CRM customer data.

    Args:
        num_rows: Number of customer records to generate
        seed: Random seed for reproducibility

    Returns:
        DataFrame with columns: customer_id, name, email, phone, country, registration_date
    """
    import random
    from datetime import datetime, timedelta

    random.seed(seed)
    pd.np.random.seed(seed)

    first_names = [
        "أحمد", "محمد", "علي", "فاطمة", "عائشة",
        "John", "Jane", "Bob", "Alice", "Charlie",
    ]
    last_names = [
        "محمود", "علي", "حسن", "عمر", "فرج",
        "Smith", "Johnson", "Williams", "Brown", "Jones",
    ]
    countries = ["SA", "AE", "EG", "US", "UK", "DE", "FR"]

    data = {
        "customer_id": range(1, num_rows + 1),
        "name": [
            f"{random.choice(first_names)} {random.choice(last_names)}"
            for _ in range(num_rows)
        ],
        "email": [
            f"customer{i}@example.com" for i in range(1, num_rows + 1)
        ],
        "phone": [
            f"+{random.randint(1, 99)}{random.randint(100000000, 999999999)}"
            for _ in range(num_rows)
        ],
        "country": [random.choice(countries) for _ in range(num_rows)],
        "registration_date": [
            (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1460))).date()
            for _ in range(num_rows)
        ],
    }

    return pd.DataFrame(data)


def generate_sales_data(num_rows: int, seed: int, num_customers: int) -> pd.DataFrame:
    """
    Generate mock sales/transaction data.

    Args:
        num_rows: Number of transaction records
        seed: Random seed for reproducibility
        num_customers: Number of customers (for valid customer_id references)

    Returns:
        DataFrame with columns: transaction_id, customer_id, amount, date, product
    """
    import random
    from datetime import datetime, timedelta

    random.seed(seed + 1)
    pd.np.random.seed(seed + 1)

    products = [
        "Product A", "Product B", "Product C", "Service X", "Service Y", "Bundle Pack"
    ]

    data = {
        "transaction_id": range(1, num_rows + 1),
        "customer_id": [
            random.randint(1, min(num_customers, num_rows))
            for _ in range(num_rows)
        ],
        "amount": [round(random.uniform(10, 5000), 2) for _ in range(num_rows)],
        "date": [
            (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))).date()
            for _ in range(num_rows)
        ],
        "product": [random.choice(products) for _ in range(num_rows)],
    }

    return pd.DataFrame(data)


@app.callback(invoke_without_command=True)
def generate_mock_data(
    rows: int = typer.Option(
        50, "--rows", "-r", help="Number of rows to generate for each dataset"
    ),
    seed: int = typer.Option(
        42, "--seed", "-s", help="Random seed for reproducible generation"
    ),
    no_xlsx: bool = typer.Option(
        False,
        "--no-xlsx",
        help="Skip Excel output (if openpyxl not available)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be generated without writing files",
    ),
) -> None:
    """
    Generate mock customer and sales data for testing.

    Generates:
    1. CRM Data (CSV): data/raw/crm_data.csv
       - customer_id, name, email, phone, country, registration_date

    2. Sales Data (Excel or CSV): data/raw/sales_data.xlsx or .csv
       - transaction_id, customer_id, amount, date, product

    Example:
        docker compose run --rm etl python -m etl_cli generate-mock-data --rows 100 --seed 42
    """
    typer.echo(f"🌱 Generating mock data (seed={seed}, rows={rows})...\n")

    # Ensure data directories exist
    try:
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/clean").mkdir(parents=True, exist_ok=True)
    except Exception as e:
        typer.echo(f"❌ Cannot create data directories: {e}", err=True)
        sys.exit(4)

    # Generate datasets
    try:
        crm_df = generate_crm_data(rows, seed)
        sales_df = generate_sales_data(rows, seed, num_customers=max(rows // 2, 10))
        typer.echo(f"✓ Generated {rows} CRM records")
        typer.echo(f"✓ Generated {rows} sales transactions")
    except Exception as e:
        typer.echo(f"❌ Error generating data: {e}", err=True)
        sys.exit(1)

    if dry_run:
        typer.echo("\n[DRY RUN] Files that would be created:")
        typer.echo("  - data/raw/crm_data.csv")
        if not no_xlsx:
            typer.echo("  - data/raw/sales_data.xlsx")
        else:
            typer.echo("  - data/raw/sales_data.csv")
        typer.echo(f"\nCRM Data Preview:\n{crm_df.head()}")
        typer.echo(f"\nSales Data Preview:\n{sales_df.head()}")
        return

    # Write CSV files
    try:
        crm_path = Path("data/raw/crm_data.csv")
        crm_df.to_csv(crm_path, index=False)
        typer.echo(f"✓ Wrote {crm_path} ({len(crm_df)} rows)")
    except Exception as e:
        typer.echo(f"❌ Error writing CRM data: {e}", err=True)
        sys.exit(4)

    # Write sales data (XLSX or CSV)
    sales_path_xlsx = Path("data/raw/sales_data.xlsx")
    sales_path_csv = Path("data/raw/sales_data.csv")

    if not no_xlsx:
        try:
            import openpyxl  # noqa: F401
            sales_df.to_excel(sales_path_xlsx, index=False, engine="openpyxl")
            typer.echo(f"✓ Wrote {sales_path_xlsx} ({len(sales_df)} rows)")
        except ImportError:
            typer.echo("⚠️  openpyxl not installed. Writing CSV instead.", err=True)
            try:
                sales_df.to_csv(sales_path_csv, index=False)
                typer.echo(f"✓ Wrote {sales_path_csv} ({len(sales_df)} rows)")
            except Exception as e:
                typer.echo(f"❌ Error writing sales data: {e}", err=True)
                sys.exit(4)
        except Exception as e:
            typer.echo(f"❌ Error writing Excel file: {e}", err=True)
            sys.exit(4)
    else:
        try:
            sales_df.to_csv(sales_path_csv, index=False)
            typer.echo(f"✓ Wrote {sales_path_csv} ({len(sales_df)} rows)")
        except Exception as e:
            typer.echo(f"❌ Error writing sales data: {e}", err=True)
            sys.exit(4)

    # Summary
    typer.echo("\n✅ Mock data generated successfully!")
    typer.echo("\nFiles created:")
    typer.echo(f"  - data/raw/crm_data.csv ({len(crm_df)} customers)")
    if not no_xlsx:
        typer.echo(
            f"  - data/raw/sales_data.xlsx ({len(sales_df)} transactions)"
        )
    else:
        typer.echo(
            f"  - data/raw/sales_data.csv ({len(sales_df)} transactions)"
        )
    typer.echo("\nNext: Run 'python -m etl_cli run-pipeline' to process the data.")
