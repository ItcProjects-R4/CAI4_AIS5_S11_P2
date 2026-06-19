# ETL Pipeline - ShopOrder Database

A production-grade ETL pipeline for loading cleaned CSV data into a PostgreSQL staging database using Docker containers and Python.

## 📋 Overview

This project implements a complete ETL (Extract, Transform, Load) solution for the shoporder database with the following features:

- **Docker-based PostgreSQL 16**: Containerized database for easy setup and portability
- **CSV-to-PostgreSQL Pipeline**: Loads 6 CSV files into 6 staging tables
- **Robust Error Handling**: Per-row fallback, transaction support, and comprehensive logging
- **Pre-flight Validation**: Automatic health checks before ETL execution
- **Data Quality Checks**: NULL detection, duplicate key detection, and summary statistics
- **Production-Ready**: Modular architecture, explicit column mapping, detailed reports

## 🗂️ Project Structure

```
etl_pipeline/
├── __init__.py
├── config.py                    # Configuration (loads from .env)
├── db_connection.py            # Database connectivity with retry logic
├── logger.py                   # Centralized logging
├── main.py                     # ETL orchestration with pre-flight checks
├── healthcheck.py              # Pre-flight validation script
├── requirements.txt            # Python dependencies
│
├── loaders/
│   ├── __init__.py
│   ├── loader_utils.py        # Reusable CSV loading utilities
│   ├── load_etl_batch.py      # Load etl_batch.csv
│   ├── load_contacts.py       # Load contacts.csv
│   ├── load_customers.py      # Load customers.csv
│   ├── load_products.py       # Load products.csv
│   ├── load_sales_orders.py   # Load sales_orders.csv
│   └── load_order_lines.py    # Load order_lines.csv
│
├── validation/
│   ├── __init__.py
│   └── validation.py          # Data quality validation functions
│
├── database/
│   ├── 01_create_database.sql       # Create database
│   ├── 02_create_staging_tables.sql # Create tables
│   ├── 03_load_data.sql             # Load data templates
│   └── 04_validation.sql            # Validation queries
│
└── execution_logs/
    ├── etl.log                # Execution log
    ├── etl_run_summary.json   # Row counts and timing
    ├── etl_verification.json  # Data quality results
    └── column_mapping.json    # CSV-to-table mappings

docker-compose.yml              # Docker PostgreSQL container definition
.env                            # Environment variables (KEEP SECRET!)
.gitignore                      # Git ignore rules
start_etl.bat                   # Windows startup script
start_etl.sh                    # Linux/Mac startup script
healthcheck.py                  # Health check runner
README.md                       # This file
```

## 🚀 Quick Start (Windows)

### Prerequisites

- Docker Desktop (installed and running)
- Python 3.8+
- Git

### 1. Clone or Download Project

```bash
cd your-project-directory
```

### 2. Start PostgreSQL with Docker

```bash
docker compose up -d
```

Wait 10-15 seconds for PostgreSQL to initialize.

### 3. Create Database and Tables

```bash
# Option A: Using psql Client (if installed)
psql -U postgres -f etl_pipeline/database/01_create_database.sql
psql -U postgres -d shoporder -f etl_pipeline/database/02_create_staging_tables.sql

# Option B: Using Docker exec
docker exec -i shoporder_postgres_16 psql -U postgres -f /docker-entrypoint-initdb.d/01_create_database.sql
docker exec -i shoporder_postgres_16 psql -U postgres -d shoporder -f /docker-entrypoint-initdb.d/02_create_staging_tables.sql
```

### 4. Run ETL Pipeline

**Option A: Automated Startup Script (Recommended)**

```bash
start_etl.bat
```

This script will:

- Verify Docker is running
- Start PostgreSQL container
- Wait for initialization
- Run health checks
- Install Python dependencies
- Execute ETL pipeline

**Option B: Manual Execution**

```bash
# Install dependencies
pip install -r etl_pipeline/requirements.txt

# Run health checks
python healthcheck.py

# Execute ETL
python -m etl_pipeline.main
```

### 5. Verify Results

Check logs and reports:

```bash
# View execution log
type etl_pipeline\\execution_logs\\etl.log

# View run summary (row counts, timing)
type etl_pipeline\\execution_logs\\etl_run_summary.json

# View data quality report
type etl_pipeline\\execution_logs\\etl_verification.json
```

Query database:

```bash
psql -U postgres -d shoporder
postgres=# SELECT COUNT(*) FROM stg_contact;
postgres=# SELECT COUNT(*) FROM stg_customer;
postgres=# \q
```

## 🚀 Quick Start (Linux/Mac)

### Prerequisites

- Docker (installed and running)
- Python 3.8+
- Git

### 1. Make startup script executable

```bash
chmod +x start_etl.sh
```

### 2. Start PostgreSQL with Docker

```bash
docker compose up -d
sleep 15
```

### 3. Create Database and Tables

```bash
psql -U postgres -f etl_pipeline/database/01_create_database.sql
psql -U postgres -d shoporder -f etl_pipeline/database/02_create_staging_tables.sql
```

### 4. Run ETL Pipeline

**Option A: Automated Startup Script (Recommended)**

```bash
./start_etl.sh
```

**Option B: Manual Execution**

```bash
pip3 install -r etl_pipeline/requirements.txt
python3 healthcheck.py
python3 -m etl_pipeline.main
```

### 5. Verify Results

```bash
cat etl_pipeline/execution_logs/etl.log
cat etl_pipeline/execution_logs/etl_run_summary.json
cat etl_pipeline/execution_logs/etl_verification.json

# Query database
psql -U postgres -d shoporder
```

## 🐳 Docker Commands

### Start PostgreSQL Container

```bash
docker compose up -d
```

### Stop PostgreSQL Container

```bash
docker compose down
```

### View Container Logs

```bash
docker compose logs -f postgres
```

### Execute Commands Inside Container

```bash
# Run PostgreSQL queries
docker exec -i shoporder_postgres_16 psql -U postgres -d shoporder -c "SELECT COUNT(*) FROM stg_contact;"

# View PostgreSQL version
docker exec shoporder_postgres_16 psql --version
```

### Remove Container and Volume

```bash
docker compose down -v
```

This will delete the PostgreSQL container and its data volume.

## ⚙️ Configuration

### .env File

Located in project root. Contains environment variables:

```env
# Database credentials
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shoporder

# Driver
DB_DRIVER=psycopg2

# Logging
LOG_LEVEL=INFO

# ETL Settings
CHUNK_SIZE=1000              # Rows per insert batch
RETRY_MAX_ATTEMPTS=3         # Connection retry attempts
RETRY_WAIT_SECONDS=5         # Base wait time (exponential backoff)
```

**For Docker PostgreSQL from another container, use**:

```env
DB_HOST=postgres  # Docker service name from docker-compose.yml
```

### Modify Credentials

Edit `.env` file to change PostgreSQL credentials:

```env
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5433  # If using custom port
```

Then rebuild and restart:

```bash
docker compose down
docker compose up -d
```

## 📊 ETL Pipeline Flow

```
START
  ↓
PRE-FLIGHT CHECKS
  ├─ Database Connectivity (with retries)
  ├─ Database Existence
  ├─ Staging Tables Existence
  └─ CSV Files Existence
  ↓
ETL_BATCH (etl_batch.csv → stg_etl_batch)
  ↓
CONTACTS (contacts.csv → stg_contact)
  ↓
CUSTOMERS (customers.csv → stg_customer)
  ↓
PRODUCTS (products.csv → stg_product)
  ↓
SALES_ORDERS (sales_orders.csv → stg_sales_order)
  ↓
ORDER_LINES (order_lines.csv → stg_order_line)
  ↓
VALIDATION & VERIFICATION
  ├─ Row Counts
  ├─ NULL Detection
  ├─ Duplicate Key Detection
  └─ Data Quality Checks
  ↓
END
```

## 📈 CSV to Staging Table Mapping

| CSV File         | Staging Table   | Rows             | Columns |
| ---------------- | --------------- | ---------------- | ------- |
| etl_batch.csv    | stg_etl_batch   | Batch metadata   | 6       |
| contacts.csv     | stg_contact     | Contact records  | 18      |
| customers.csv    | stg_customer    | Customer records | 10      |
| products.csv     | stg_product     | Product records  | 13      |
| sales_orders.csv | stg_sales_order | Order records    | 11      |
| order_lines.csv  | stg_order_line  | Order line items | 6       |

All mappings are explicit in loader modules with zero ambiguity.

## 🔍 Health Check

Run health check to verify system readiness:

```bash
python healthcheck.py
```

This checks:

- Directory structure (logs, reports, diagrams)
- All 6 CSV files exist
- Database connectivity
- Database existence
- All 6 staging tables exist

Output example:

```
================================================================================
CHECKING DIRECTORIES
================================================================================
✓ etl_pipeline/execution_logs
✓ reports
✓ etl_pipeline/architecture
✓ cleaned_data/

================================================================================
CHECKING CSV FILES
================================================================================
✓ etl_batch.csv                       (0.00 MB)
✓ contacts.csv                        (3.45 MB)
✓ customers.csv                       (0.15 MB)
✓ products.csv                        (0.08 MB)
✓ sales_orders.csv                    (0.12 MB)
✓ order_lines.csv                     (0.22 MB)

================================================================================
CHECKING DATABASE CONNECTION
================================================================================
✓ Database connection successful (attempt 1)

================================================================================
CHECKING DATABASE
================================================================================
✓ Database 'shopOrder' verified

================================================================================
CHECKING STAGING TABLES
================================================================================
✓ stg_etl_batch
✓ stg_contact
✓ stg_customer
✓ stg_product
✓ stg_sales_order
✓ stg_order_line

Health Check Summary
================================================================================
✓ PASS Directories
✓ PASS CSV Files
✓ PASS Database Connection
✓ PASS Database Exists
✓ PASS Staging Tables

Passed: 5/5

✓ All checks passed! ETL is ready to run.
  Execute: python -m etl_pipeline.main
```

## 📝 Log Files

### etl.log

Main execution log with all DEBUG, INFO, WARNING, ERROR messages.

```bash
cat etl_pipeline/execution_logs/etl.log
```

### etl_run_summary.json

Row counts, timing, and failures for each loader.

```json
{
  "etl_pipeline.loaders.load_etl_batch": {
    "table": "stg_etl_batch",
    "csv": ".../cleaned_data/etl_batch.csv",
    "rows_read": 2,
    "rows_inserted": 2,
    "rows_failed": 0,
    "duration_s": 0.523,
    "status": "loaded"
  },
  "etl_pipeline.loaders.load_contacts": {
    "table": "stg_contact",
    "csv": ".../cleaned_data/contacts.csv",
    "rows_read": 1000,
    "rows_inserted": 1000,
    "rows_failed": 0,
    "duration_s": 2.145,
    "status": "loaded"
  }
}
```

### etl_verification.json

Post-load data quality results.

```json
{
  "stg_contact": {
    "rows": 1000,
    "nulls": { "phone": 50 },
    "duplicates": 0,
    "dq_issues": {}
  }
}
```

## 🐛 Troubleshooting

### Issue: "Cannot connect to Docker container"

**Error Message:**

```
✗ Failed to connect to PostgreSQL at localhost:5432 after 3 attempts
```

**Solutions:**

1. Verify Docker is running:

```bash
docker ps
```

2. Start PostgreSQL container:

```bash
docker compose up -d
docker compose logs -f postgres
```

3. Wait 15 seconds for PostgreSQL to initialize
4. Verify container is healthy:

```bash
docker compose ps
# STATUS should show "healthy"
```

### Issue: "Missing staging tables"

**Error Message:**

```
✗ Missing staging tables: ['stg_contact', 'stg_customer', ...]
```

**Solutions:**

1. Create tables:

```bash
docker exec -i shoporder_postgres_16 psql -U postgres -d shoporder -f /docker-entrypoint-initdb.d/02_create_staging_tables.sql
```

2. Verify tables created:

```bash
docker exec shoporder_postgres_16 psql -U postgres -d shoporder -c "\dt"
```

### Issue: "CSV files not found"

**Error Message:**

```
✗ contacts.csv - NOT FOUND
```

**Solutions:**

1. Verify directory structure:

```bash
ls -la cleaned_data/
```

2. Ensure all CSV files are in `./cleaned_data/` directory:
   - etl_batch.csv
   - contacts.csv
   - customers.csv
   - products.csv
   - sales_orders.csv
   - order_lines.csv

### Issue: "Permission denied" on start_etl.sh

**Error Message:**

```
bash: ./start_etl.sh: Permission denied
```

**Solution:**

Make script executable:

```bash
chmod +x start_etl.sh
./start_etl.sh
```

### Issue: "Port 5432 already in use"

**Error Message:**

```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5432 -> 0.0.0.0:0: listen tcp 0.0.0.0:5432: bind: An address is already in use
```

**Solutions:**

1. Stop the conflicting container:

```bash
docker ps
docker stop <container_id>
```

2. Or use a different port in `.env`:

```env
DB_PORT=5433
```

Then rebuild:

```bash
docker compose down
docker compose up -d
```

### Issue: "Out of memory" during ETL

**Error Message:**

```
MemoryError or connection timeout
```

**Solutions:**

1. Reduce batch size in `.env`:

```env
CHUNK_SIZE=500  # Smaller chunks = less memory
```

2. Increase Docker memory:
   - Docker Desktop → Settings → Resources → Memory
   - Set to 4GB or higher

3. Re-run:

```bash
docker compose restart
python -m etl_pipeline.main
```

### Issue: "Python dependencies not found"

**Error Message:**

```
ModuleNotFoundError: No module named 'pandas'
```

**Solutions:**

1. Install dependencies:

```bash
pip install -r etl_pipeline/requirements.txt
# or
pip3 install -r etl_pipeline/requirements.txt
```

2. Verify installation:

```bash
python -m pip list | grep pandas
```

### Issue: "Database already exists"

**Error Message:**

```
ERROR: database "shoporder" already exists
```

**Solution (non-destructive):**

The SQL script uses `DROP DATABASE IF EXISTS`, so just re-run:

```bash
psql -U postgres -f etl_pipeline/database/01_create_database.sql
psql -U postgres -d shoporder -f etl_pipeline/database/02_create_staging_tables.sql
```

**Solution (if you want to reset):**

```bash
psql -U postgres
postgres=# DROP DATABASE IF EXISTS shoporder;
postgres=# \q

psql -U postgres -f etl_pipeline/database/01_create_database.sql
psql -U postgres -d shoporder -f etl_pipeline/database/02_create_staging_tables.sql
```

## 📊 Viewing Results

### Query data in PostgreSQL

```bash
psql -U postgres -d shoporder

shoporder=# SELECT COUNT(*) as contact_count FROM stg_contact;
shoporder=# SELECT COUNT(*) as customer_count FROM stg_customer;
shoporder=# SELECT COUNT(*) as product_count FROM stg_product;
shoporder=# SELECT COUNT(*) as order_count FROM stg_sales_order;
shoporder=# SELECT COUNT(*) as line_count FROM stg_order_line;

shoporder=# SELECT * FROM stg_contact LIMIT 5;
```

### Export data to CSV

```bash
psql -U postgres -d shoporder -c "COPY stg_contact TO STDOUT WITH CSV HEADER;" > contacts_dump.csv
```

### View execution reports

```bash
# Windows
type etl_pipeline\\execution_logs\\etl_run_summary.json
type etl_pipeline\\execution_logs\\etl_verification.json

# Linux/Mac
cat etl_pipeline/execution_logs/etl_run_summary.json
cat etl_pipeline/execution_logs/etl_verification.json
```

## 🔐 Security Notes

1. **Never commit .env file** - it contains database credentials
   - `.gitignore` already includes `.env`
   - Use `cp .env .env.example` for version control

2. **Change default credentials** in `.env` for production:

   ```env
   DB_USER=postgres
   DB_PASSWORD=strong_password_here
   ```

3. **Restrict database access** in production
4. **Use Docker secrets** instead of .env for production deployments

## 📞 Support

For issues:

1. Run health check: `python healthcheck.py`
2. Check logs: `etl_pipeline/execution_logs/etl.log`
3. Verify Docker: `docker compose logs -f postgres`
4. Consult troubleshooting section above

## 📄 License

This project is part of the ITC DEPI R4 curriculum.

---

**Last Updated:** 2026-06-19
**Version:** 1.0.0
**Status:** Production Ready
