# SETUP_GUIDE.md

## Getting Started with Customer Data ETL

This document provides step-by-step instructions to set up and start using the Customer Data ETL project.

---

## Prerequisites

- **Docker** and **Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Git** for version control
- A text editor (VS Code, nano, etc.)
- ~2 GB disk space for the Docker image and data

---

## Step 1: Verify Docker Installation

```bash
docker --version
docker compose --version
```

Expected output:
```
Docker version 24.0+
Docker Compose version 2.20+
```

---

## Step 2: Clone or Navigate to Repository

```bash
cd /home/alih/Learning/customer-data-etl
pwd  # Should show /home/alih/Learning/customer-data-etl
```

---

## Step 3: Set Up Environment

### 3a. Copy .env.template to .env

```bash
cp .env.template .env
```

### 3b. Edit .env with Your Credentials (Optional for Development)

For initial testing with mock data, the default .env.template values will work.

If you have a SQL Server instance to test against:

```bash
nano .env
# Edit: DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD
```

Press `Ctrl+O` then `Enter` to save, `Ctrl+X` to exit nano.

---

## Step 4: Build the Docker Image

```bash
docker compose build
```

Or use the Makefile shortcut:

```bash
make build
```

This downloads the Python 3.10 base image and installs all dependencies from `pyproject.toml`. It may take 2-3 minutes on first build.

**Expected output:**
```
 => => writing image sha256:abc123...
 => => naming to docker.io/customer-data-etl:latest
Successfully built ...
```

---

## Step 5: Verify Environment Setup

```bash
docker compose run --rm etl python -m etl_cli check_env
```

Or:

```bash
make check-env
```

**Expected output:**
```
🔍 Checking environment...

✓ Python 3.10
✓ typer installed
✓ pandas installed
✓ openpyxl installed
✓ python-dotenv installed

...

✅ All checks passed! Environment is ready.
```

---

## Step 6: Generate Mock Data

```bash
docker compose run --rm etl python -m etl_cli generate_mock_data --rows 50 --seed 42
```

Or:

```bash
make mock-data
```

**Expected output:**
```
🌱 Generating mock data (seed=42, rows=50)...

✓ Generated 50 CRM records
✓ Generated 50 sales transactions
✓ Wrote data/raw/crm_data.csv (50 rows)
✓ Wrote data/raw/sales_data.xlsx (50 rows)

✅ Mock data generated successfully!
```

**Verify files were created:**

```bash
ls -lh data/raw/
```

---

## Step 7: Run Tests

```bash
docker compose run --rm etl pytest
```

Or:

```bash
make test
```

**Expected output:**
```
collected 25 items

tests/test_check_env.py ......
tests/test_generate_mock_data.py ...................

======================== 25 passed in 1.23s ========================
```

---

## Step 8: Open an Interactive Shell

For interactive development:

```bash
docker compose run --rm etl bash
```

Or:

```bash
make shell
```

You're now inside the container. Try commands like:

```bash
# View project structure
ls -la

# Check Python version
python --version

# Run CLI commands
python -m etl_cli --help

# Exit
exit
```

---

## Step 9: Run the ETL Pipeline (Placeholder)

```bash
docker compose run --rm etl python -m etl_cli run_pipeline
```

**Expected output:**
```
🔄 Starting ETL Pipeline...

📥 Extract phase...
  ✓ Found data/raw/crm_data.csv
  ✓ Found data/raw/sales_data.xlsx
  ✓ Extraction complete
⚙️  Transform phase...
  • Deduplicate customer records (placeholder)
  • Validate email addresses (placeholder)
  • Enrich with geolocation data (stub)
  • Calculate customer lifetime value (stub)
  ✓ Transformation complete
📤 Load phase...
  • Would write to data/clean/customer_dim.csv (placeholder)
  • Would write to data/clean/transaction_fact.csv (placeholder)
  • Would insert into warehouse_db.dbo.customers (placeholder)
  ✓ Load complete
✔️  Validate phase...
  ✓ No null customer IDs
  ✓ No duplicate transactions
  ✓ Email format valid
  ✓ Amount > 0
  ✓ 4/4 checks passed

✅ Pipeline complete!
```

---

## Step 10: Check Code Quality

### Lint (flake8)

```bash
docker compose run --rm etl flake8 src tests
```

### Format Check (Black & isort)

```bash
docker compose run --rm etl black --check src tests
docker compose run --rm etl isort --check-only src tests
```

### Auto-Format Code

```bash
docker compose run --rm etl bash -c "black src tests && isort src tests"
```

Or:

```bash
make fmt
```

---

## Common Commands

| Command | Purpose |
|---------|---------|
| `make build` | Build Docker image |
| `make shell` | Interactive shell in container |
| `make test` | Run tests |
| `make lint` | Check code style |
| `make fmt` | Format code |
| `make check-env` | Diagnose environment |
| `make mock-data` | Generate mock data |
| `make clean` | Delete generated data files |
| `make clean-docker` | Stop containers, remove volumes |

---

## Development Workflow

### 1. Make Changes

Edit files in `src/etl_cli/` or `tests/` using your local editor.

### 2. Test Changes Inside Docker

```bash
make shell
pytest
flake8 src tests
black --check src tests
```

### 3. Commit Changes

```bash
git add .
git commit -m "Feature: add new transformer module"
```

### 4. Push and Create PR

```bash
git push origin feature/my-feature
# Then create PR on GitHub
```

---

## Troubleshooting

### Issue: `docker: command not found`

**Solution:** Install Docker from https://docs.docker.com/get-docker/

### Issue: `Port 5432 already in use`

**Solution:** No ports are exposed in the current setup. If you add a database service, modify `docker-compose.yml` to use a different port.

### Issue: Tests fail with `ModuleNotFoundError`

**Cause:** Dependencies not installed in Docker image
**Solution:** Rebuild the image with `make clean-docker && make build`

### Issue: `.env` accidentally committed

If you committed `.env` with credentials:

```bash
# Remove it from git history (careful!)
git rm --cached .env
git commit --amend

# Add to .gitignore (already done)
# Then tell git to ignore future changes
git update-index --skip-worktree .env
```

### Issue: Permission denied when writing to `data/`

**Cause:** Running commands on host instead of in Docker
**Solution:** Always run commands inside Docker with `docker compose run --rm etl`

### Issue: Tests pass locally but fail in CI

**Cause:** Different environment or missing dependencies
**Solution:** Check `pyproject.toml` has all dependencies listed. Rebuild Docker image.

---

## Project Structure Summary

```
customer-data-etl/
├── README.md                          # Main documentation
├── SETUP_GUIDE.md                     # This file
├── CONTRIBUTING.md                    # Contribution guidelines
├── CODE_OF_CONDUCT.md                 # Community standards
├── LICENSE                            # MIT license
├── .env.template                      # Environment variable template
├── .env                               # Local env config (git-ignored)
├── .gitignore                         # Git ignore rules
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI/CD
├── pyproject.toml                     # Dependencies & config
├── docker-compose.yml                 # Docker Compose config
├── Makefile                           # Development shortcuts
├── docker/
│   ├── Dockerfile                     # Docker image definition
│   └── entrypoint.sh                  # Container entry script
├── src/
│   ├── __init__.py
│   └── etl_cli/
│       ├── __init__.py
│       ├── __main__.py                # CLI entry point
│       ├── setup.py                   # Setup utilities
│       ├── check_env.py               # Environment diagnostics
│       ├── generate_mock_data.py      # Mock data generation
│       └── pipeline.py                # ETL pipeline skeleton
├── tests/
│   ├── __init__.py
│   ├── test_check_env.py              # Tests for check_env
│   └── test_generate_mock_data.py     # Tests for mock data gen
├── data/
│   ├── raw/                           # Input data (mock or real)
│   └── clean/                         # Processed data output
└── sql/
    └── README.md                      # SQL scripts placeholder
```

---

## Next Steps

1. **Phase 2:** Generate mock data and explore the project
   ```bash
   make mock-data
   ls data/raw/
   ```

2. **Phase 3:** Understand the environment diagnostics
   ```bash
   make check-env
   ```

3. **Phase 4:** Implement ETL business logic
   - Edit `src/etl_cli/pipeline.py` to add real extraction/transformation
   - Edit `src/etl_cli/generate_mock_data.py` for realistic test data
   - Add SQL scripts to `sql/` for data warehouse operations

4. **Phase 5:** Connect to a real database
   - Update `.env` with actual credentials
   - Modify `pipeline.py` to connect and load data
   - Test with `make test` and `make lint`

---

## Getting Help

- **README.md** - Project overview and quick commands
- **CONTRIBUTING.md** - Code standards and PR guidelines
- **CLI Help:**
  ```bash
  docker compose run --rm etl python -m etl_cli --help
  docker compose run --rm etl python -m etl_cli generate-mock-data --help
  ```

---

## That's It!

Your development environment is ready! Start by running tests and exploring the code structure. Happy coding! 🚀
