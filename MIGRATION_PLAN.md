# MIGRATION_PLAN.md

## Migration to Docker-First Workflow

This document describes how to safely transition from any legacy scripting approach to the new Docker-first, production-grade ETL project structure.

---

## Overview

The new project provides:
- **Container-first** development (no host system dependencies)
- **Reproducible** builds (same environment for all developers)
- **CI/CD ready** (GitHub Actions workflow included)
- **Professional structure** (modular code, tests, linting)
- **Security focused** (no secrets in repo, .gitignore, pre-commit hooks)

This guide assumes you have existing scripts or manual processes that you want to archive before adopting the new structure.

---

## Phase 1: Backup Legacy Code

### Step 1.1: Create Archive Directory

```bash
cd ~/Learning/customer-data-etl
mkdir -p archive/pre_docker_reset

# If you have old scripts in the repo root, move them
if [ -f "old_etl.py" ]; then
    mv old_etl.py archive/pre_docker_reset/
    mv old_requirements.txt archive/pre_docker_reset/
    # ... move other legacy files
fi
```

### Step 1.2: Document Legacy Process

Create `archive/README_LEGACY.md`:

```bash
cat > archive/README_LEGACY.md << 'EOF'
# Legacy ETL Scripts (Pre-Docker)

These files represent the old ETL approach before containerization.

## Files
- old_etl.py - Original ETL script
- old_requirements.txt - Dependencies (may have conflicts with new ones)
- old_config.ini - Old configuration format

## Why Archived?
The new project (Phase 1+) uses Docker for reproducibility and professional deployment.
Legacy scripts are kept here for reference during transition.

## Restoring Legacy Scripts

If you need to restore the old environment:

```bash
# Copy files back to root
cp old_etl.py ../
cp old_requirements.txt ../

# Create legacy venv
python3 -m venv legacy_env
source legacy_env/bin/activate
pip install -r old_requirements.txt
python old_etl.py
```

## Migration Decisions

Review the following when migrating:
1. **Data Source Changes**: Did source systems change? Update generate_mock_data.py
2. **Transformation Logic**: Move business logic from old_etl.py to src/etl_cli/pipeline.py
3. **Dependencies**: Compare old_requirements.txt with pyproject.toml
4. **Tests**: Did the old code have any? Add to tests/
5. **Secrets**: Update .env.template with any new variables from old_config.ini

See ../SETUP_GUIDE.md and ../README.md for the new workflow.
EOF
```

### Step 1.3: Commit Archive to Git

```bash
git add archive/
git commit -m "Archive: backup legacy ETL scripts before Docker migration"
```

---

## Phase 2: Test New Docker Environment

### Step 2.1: Verify Docker Build

```bash
docker compose build
# Takes 2-3 minutes on first build
```

### Step 2.2: Run Basic Checks

```bash
# Check environment
docker compose run --rm etl python -m etl_cli check_env

# Generate test data
docker compose run --rm etl python -m etl_cli generate_mock_data --rows 10 --seed 42

# Run tests
docker compose run --rm etl pytest
```

### Step 2.3: Verify Project Structure

```bash
# List key files
ls -la src/etl_cli/
ls -la tests/
ls -la data/

# Expected output shows our new modules
tree -L 2 -I '__pycache__|*.pyc'
```

---

## Phase 3: Migrate Business Logic

### Step 3.1: Analyze Old Code

Examine your legacy ETL script:

```bash
# Read old ETL script (example)
cat archive/pre_docker_reset/old_etl.py | head -100

# Identify the major phases:
# 1. Extract - Read from CRM/Excel/DB
# 2. Transform - Clean, deduplicate, enrich
# 3. Load - Write to warehouse
```

### Step 3.2: Implement Extract Logic

Edit `src/etl_cli/pipeline.py` and replace the `extract()` placeholder:

```python
def extract():
    """Extract phase: Load data from your actual sources."""
    typer.echo("📥 Extract phase...")
    
    # Replace this with your actual extraction code
    # from old_etl.py:
    
    # Example: Read from SQL Server
    # conn = pyodbc.connect(os.getenv('DB_CONNECTION_STRING'))
    # df_crm = pd.read_sql("SELECT * FROM CRM_CUSTOMERS", conn)
    
    # Example: Read Excel with validation
    # df_sales = pd.read_excel('data/raw/sales_data.xlsx')
    
    typer.echo("  ✓ Extracted CRM data")
    typer.echo("  ✓ Extracted sales data")
    return df_crm, df_sales  # Return DataFrames
```

### Step 3.3: Implement Transform Logic

Create a new module `src/etl_cli/transform.py`:

```python
"""Data transformation and cleaning logic."""

def clean_customer_names(df):
    """Remove duplicates and trim whitespace."""
    df['name'] = df['name'].str.strip()
    df = df.drop_duplicates(subset=['customer_id'])
    return df

def enrich_with_location(df):
    """Add geolocation based on country code."""
    # Implement your enrichment logic here
    return df

def deduplicate_transactions(df):
    """Remove duplicate transactions within date windows."""
    # Implement your dedup logic
    return df
```

Then update `pipeline.py` to use these:

```python
from etl_cli.transform import clean_customer_names, enrich_with_location

def transform(df_crm, df_sales):
    """Transform phase using business logic."""
    typer.echo("⚙️  Transform phase...")
    
    df_crm = clean_customer_names(df_crm)
    df_crm = enrich_with_location(df_crm)
    
    # ... more transformations
    
    return df_crm, df_sales
```

### Step 3.4: Update Mock Data Generator

If your real data has different structure, update `generate_mock_data.py`:

```python
def generate_crm_data(num_rows: int, seed: int) -> pd.DataFrame:
    """Generate mock CRM data matching your schema."""
    # Add your actual columns here
    data = {
        'customer_id': range(1, num_rows + 1),
        'name': [...],
        'email': [...],
        # ... any custom columns your code uses
    }
    return pd.DataFrame(data)
```

### Step 3.5: Implement Load Logic

Update `pipeline.py` to load to your data warehouse:

```python
def load(df_customer, df_transaction):
    """Load phase: Write to warehouse."""
    typer.echo("📤 Load phase...")
    
    try:
        # Connect to SQL Server
        import pyodbc
        conn = pyodbc.connect(os.getenv('DB_CONNECTION_STRING'))
        
        # Load dimension table
        df_customer.to_sql('dim_customer', conn, if_exists='append')
        
        # Load fact table
        df_transaction.to_sql('fact_transaction', conn, if_exists='append')
        
        conn.close()
        typer.echo("  ✓ Data loaded to warehouse")
        return True
    except Exception as e:
        typer.echo(f"  ❌ Load failed: {e}", err=True)
        return False
```

---

## Phase 4: Migrate Tests

### Step 4.1: Convert Old Test Cases

If you had manual tests or unit tests, add them to `tests/`:

```python
# tests/test_pipeline_integration.py

def test_customer_deduplication():
    """Test that duplicate customers are removed."""
    from etl_cli.transform import clean_customer_names
    
    # Create test data with duplicates
    test_data = pd.DataFrame({
        'customer_id': [1, 1, 2],
        'name': ['  John  ', 'John', 'Jane'],
    })
    
    result = clean_customer_names(test_data)
    
    assert len(result) == 2  # Duplicates removed
    assert result.loc[0, 'name'] == 'John'  # Whitespace trimmed
```

### Step 4.2: Run Tests

```bash
# Run all tests
docker compose run --rm etl pytest

# Run with coverage
docker compose run --rm etl pytest --cov=src
```

---

## Phase 5: Update Environment Configuration

### Step 5.1: Map Old Config to .env.template

If you had `old_config.ini`:

```ini
[database]
server=sql.example.com,1433
database=etl_db
user=sa
```

Map to `.env`:

```bash
# Edit .env.template to add any new variables
DB_SERVER=sql.example.com,1433
DB_NAME=etl_db
DB_USER=sa
DB_PASSWORD=YourPasswordHere
```

### Step 5.2: Update pyproject.toml

If old code used different libraries, update dependencies:

```toml
[project]
dependencies = [
    "typer[all]>=0.9.0",
    "python-dotenv>=1.0.0",
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
    "pyodbc>=5.0.0",
    # Add any other dependencies from old_requirements.txt
]
```

Then rebuild Docker:

```bash
docker compose build
```

---

## Phase 6: Final Validation

### Step 6.1: Run Full Test Suite

```bash
docker compose run --rm etl pytest -v
docker compose run --rm etl flake8 src tests
docker compose run --rm etl black --check src tests
```

### Step 6.2: Test ETL Pipeline End-to-End

```bash
# Generate test data
docker compose run --rm etl python -m etl_cli generate_mock_data --rows 100 --seed 42

# Run pipeline
docker compose run --rm etl python -m etl_cli run_pipeline

# Verify output
ls -la data/clean/
```

### Step 6.3: Verify CI/CD

Push to GitHub and check that workflows pass:

```bash
git push origin main
# Check Actions tab on GitHub
```

---

## Phase 7: Archive Complete - Switch to New Workflow

### Step 7.1: Clean Up Old Files (Optional)

Once you're confident the new code works:

```bash
# Keep old files archived
ls -la archive/pre_docker_reset/

# Don't delete them yet, but stop using them
echo "Old scripts archived but kept for reference"
```

### Step 7.2: Document Migration Decisions

Create `MIGRATION_NOTES.md`:

```bash
cat > MIGRATION_NOTES.md << 'EOF'
# Migration Notes

## What Changed

### Structure
- Old: Single script `old_etl.py`
- New: Modular CLI with `src/etl_cli/`

### Dependencies
- Old: `pip install -r requirements.txt` (on host)
- New: `docker compose build` (containerized)

### Configuration
- Old: `config.ini` file
- New: `.env` environment variables

### Testing
- Old: Manual testing or pytest in `tests/` folder
- New: Full CI/CD with GitHub Actions

### Deployment
- Old: Run on server, hope dependencies work
- New: `docker compose run` everywhere, guaranteed to work

## Code Changes Made

1. **Extract**: Migrated from `old_etl.py` line 42-100
2. **Transform**: Created new `src/etl_cli/transform.py` module
3. **Load**: Implemented in `src/etl_cli/pipeline.py`
4. **Tests**: Added 25 unit tests covering all modules

## When to Use Archive

You can reference `archive/pre_docker_reset/old_etl.py` if:
- You forget how a calculation was done
- You need to restore the old behavior for reverse ETL
- You're auditing code changes

## Restore Old Code (Not Recommended)

If you desperately need the old setup:

```bash
cd archive/pre_docker_reset
python3 -m venv legacy_env
source legacy_env/bin/activate
pip install -r old_requirements.txt
python old_etl.py
```

But use the new Docker approach instead!
EOF

git add MIGRATION_NOTES.md
git commit -m "Docs: migration notes from legacy to Docker-first workflow"
```

---

## Rollback Plan

If something goes wrong, you can always restore:

```bash
# See git history
git log --oneline | head -20

# Restore to before migration
git reset --hard <commit-hash-before-migration>

# Your old files are still in archive/
ls archive/pre_docker_reset/
```

---

## Summary: Old → New

| Aspect | Old | New |
|--------|-----|-----|
| **Development** | Run Python on host | Run in Docker container |
| **Dependencies** | pip, system packages | Docker image (automatic) |
| **Config** | config.ini, env vars | .env file (git-ignored) |
| **Testing** | Optional, manual | Automated, pytest, CI/CD |
| **Deployment** | Pray deps work | `docker compose run` works everywhere |
| **Team Onboarding** | "Install Python 3.10, pyodbc, ..." | "Install Docker, then run setup" |
| **Production** | Docker? Maybe... | Docker by design |

---

## What's Next?

1. **Follow SETUP_GUIDE.md** to get Docker working
2. **Follow Phase 3 above** to migrate your business logic
3. **Run tests** to ensure correctness
4. **Deploy with confidence** knowing it will work everywhere

Good luck with your migration! 🚀
