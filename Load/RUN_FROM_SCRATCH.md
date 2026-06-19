# PostgreSQL ETL - Run From Scratch

## Complete Step-by-Step Guide

This document contains all commands required to run the PostgreSQL ETL pipeline from a clean state.

---

## Prerequisites

- Docker Desktop or Docker Engine installed and running
- Python 3.8+ installed
- Git (optional, for cloning)

---

## Step 1: Navigate to Project Directory

```bash
cd Load
```

---

## Step 2: Start Docker Container (PostgreSQL)

```bash
docker compose up -d
```

**Output**: PostgreSQL container starts in background

**Verify**:

```bash
docker compose ps
# STATUS should show "healthy" after 15 seconds
```

---

## Step 3: Wait for PostgreSQL Initialization

```bash
sleep 15
```

---

## Step 4: Create Database and Tables

PostgreSQL automatically initializes the database on first start using files in `etl_pipeline/database/`

**Verify database created**:

```bash
docker exec shoporder_postgres_16 psql -U postgres -d shoporder -c "\dt"
```

**Expected output**: List of 6 tables (stg_etl_batch, stg_contact, stg_customer, stg_product, stg_sales_order, stg_order_line)

---

## Step 5: Install Python Dependencies

```bash
pip install -r etl_pipeline/requirements.txt
```

**Or for Python 3 specifically**:

```bash
pip3 install -r etl_pipeline/requirements.txt
```

**Expected packages installed**:

- pandas>=2.0.0
- SQLAlchemy>=2.0.0
- psycopg2-binary>=2.9.0
- python-dotenv>=1.0.0

---

## Step 6: Run Health Check

```bash
python healthcheck.py
```

**Expected output**:

```
✓ PASS Directories
✓ PASS CSV Files
✓ PASS Database Connection
✓ PASS Database Exists
✓ PASS Staging Tables
Passed: 5/5
✓ All checks passed! ETL is ready to run.
```

---

## Step 7: Execute ETL Pipeline

```bash
python -m etl_pipeline.main
```

**Or using Python 3 specifically**:

```bash
python3 -m etl_pipeline.main
```

**Expected output**:

```
================================================================================
PRE-FLIGHT CHECKS
================================================================================
1. Testing database connectivity...
   ✓ Database connection successful (attempt 1)

2. Verifying database exists...
   ✓ Database 'shoporder' verified

3. Verifying staging tables...
   ✓ All 6 staging tables verified

4. Verifying required CSV files...
   ✓ All 6 CSV files verified

================================================================================
ETL PIPELINE EXECUTION
================================================================================

[Loader 1/6] Loading etl_batch.csv → stg_etl_batch
✓ Loaded successfully: X rows

[Loader 2/6] Loading contacts.csv → stg_contact
✓ Loaded successfully: X rows

[Loader 3/6] Loading customers.csv → stg_customer
✓ Loaded successfully: X rows

[Loader 4/6] Loading products.csv → stg_product
✓ Loaded successfully: X rows

[Loader 5/6] Loading sales_orders.csv → stg_sales_order
✓ Loaded successfully: X rows

[Loader 6/6] Loading order_lines.csv → stg_order_line
✓ Loaded successfully: X rows

================================================================================
VALIDATION & VERIFICATION
================================================================================

Table stg_etl_batch: X rows, 0 NULLs, 0 duplicates
Table stg_contact: X rows, X NULLs, 0 duplicates
Table stg_customer: X rows, X NULLs, 0 duplicates
Table stg_product: X rows, 0 NULLs, 0 duplicates
Table stg_sales_order: X rows, 0 NULLs, 0 duplicates
Table stg_order_line: X rows, 0 NULLs, 0 duplicates

✓ ETL completed successfully!
```

---

## Step 8: Verify Results

### Check CSV Files Loaded

```bash
docker exec shoporder_postgres_16 psql -U postgres -d shoporder -c "
SELECT 'stg_etl_batch' AS table_name, COUNT(*) FROM stg_etl_batch
UNION ALL
SELECT 'stg_contact', COUNT(*) FROM stg_contact
UNION ALL
SELECT 'stg_customer', COUNT(*) FROM stg_customer
UNION ALL
SELECT 'stg_product', COUNT(*) FROM stg_product
UNION ALL
SELECT 'stg_sales_order', COUNT(*) FROM stg_sales_order
UNION ALL
SELECT 'stg_order_line', COUNT(*) FROM stg_order_line;
"
```

### View Execution Logs

```bash
# Windows
type etl_pipeline\execution_logs\etl.log
type etl_pipeline\execution_logs\etl_run_summary.json

# Linux/Mac
cat etl_pipeline/execution_logs/etl.log
cat etl_pipeline/execution_logs/etl_run_summary.json
```

### Query Sample Data

```bash
docker exec shoporder_postgres_16 psql -U postgres -d shoporder -c "SELECT * FROM stg_contact LIMIT 5;"
```

---

## 🎯 Automated Startup Scripts

Instead of running steps manually, use the provided startup scripts:

### Windows

```batch
start_etl.bat
```

This script automatically:

1. Checks Docker installation
2. Starts the container
3. Waits 15 seconds
4. Runs health checks
5. Installs dependencies
6. Executes ETL
7. Shows results

### Linux/Mac

```bash
chmod +x start_etl.sh
./start_etl.sh
```

Same as Windows script, in bash format.

---

## 🛑 Stopping the Pipeline

### Stop Docker Container (Keeps Data)

```bash
docker compose down
```

### Stop and Remove All Data

```bash
docker compose down -v
```

---

## 🔄 Restarting After First Run

To run ETL again without recreating the container:

```bash
# Just run the ETL (assumes container is running)
python -m etl_pipeline.main
```

To completely restart:

```bash
# Stop and remove
docker compose down -v

# Start fresh
docker compose up -d
sleep 15
python healthcheck.py
python -m etl_pipeline.main
```

---

## 🔍 Useful PostgreSQL Commands

### Connect to Database

```bash
docker exec -it shoporder_postgres_16 psql -U postgres -d shoporder
```

Then use psql commands:

```sql
-- List tables
\dt

-- Show table structure
\d stg_contact

-- Query row counts
SELECT COUNT(*) FROM stg_contact;

-- Exit
\q
```

### Query Without Interactive Session

```bash
docker exec shoporder_postgres_16 psql -U postgres -d shoporder -c "SELECT COUNT(*) FROM stg_contact;"
```

### Backup Database

```bash
docker exec shoporder_postgres_16 pg_dump -U postgres -d shoporder > shoporder_backup.sql
```

### Restore Database

```bash
docker exec -i shoporder_postgres_16 psql -U postgres -d shoporder < shoporder_backup.sql
```

### Export Table to CSV

```bash
docker exec shoporder_postgres_16 psql -U postgres -d shoporder \
  -c "COPY stg_contact TO STDOUT WITH CSV HEADER;" > contacts_export.csv
```

---

## 🔧 Configuration Changes

To modify database credentials, edit `.env`:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
DB_HOST=localhost
DB_NAME=shoporder
DB_DRIVER=psycopg2
```

Then restart:

```bash
docker compose down -v
docker compose up -d
sleep 15
python -m etl_pipeline.main
```

---

## 📊 Directory Structure

```
Load/
├── .env                          # Configuration (KEEP SECRET!)
├── .env.example                  # Configuration template
├── docker-compose.yml            # PostgreSQL container definition
├── start_etl.bat                 # Windows startup script
├── start_etl.sh                  # Linux/Mac startup script
├── healthcheck.py                # Pre-flight verification
├── README.md                      # Full documentation
├── MIGRATION_REPORT.md           # Technical migration details
├── MIGRATION_SUMMARY.md          # Migration overview
│
├── etl_pipeline/
│   ├── main.py                   # ETL orchestration
│   ├── config.py                 # Configuration loader
│   ├── db_connection.py          # PostgreSQL connection
│   ├── logger.py                 # Logging utilities
│   ├── requirements.txt          # Python dependencies
│   │
│   ├── loaders/                  # CSV loading modules
│   │   ├── load_etl_batch.py
│   │   ├── load_contacts.py
│   │   ├── load_customers.py
│   │   ├── load_products.py
│   │   ├── load_sales_orders.py
│   │   ├── load_order_lines.py
│   │   └── loader_utils.py
│   │
│   ├── validation/               # Data quality validation
│   │   └── validation.py
│   │
│   ├── database/                 # SQL initialization scripts
│   │   ├── 01_create_database.sql
│   │   ├── 02_create_staging_tables.sql
│   │   ├── 03_load_data.sql
│   │   └── 04_validation.sql
│   │
│   └── execution_logs/           # Outputs (created on first run)
│       ├── etl.log
│       ├── etl_run_summary.json
│       └── etl_verification.json
│
├── cleaned_data/                 # Input CSV files
│   ├── etl_batch.csv
│   ├── contacts.csv
│   ├── customers.csv
│   ├── products.csv
│   ├── sales_orders.csv
│   └── order_lines.csv
│
└── reports/                      # Output reports directory
```

---

## 🚨 Troubleshooting

### Error: "Docker command not found"

**Solution**: Install Docker from https://www.docker.com/

### Error: "Cannot connect to PostgreSQL"

**Solution**:

```bash
docker compose logs -f postgres
sleep 10
python healthcheck.py
```

### Error: "Python module not found"

**Solution**:

```bash
pip install -r etl_pipeline/requirements.txt
```

### Error: "Port 5432 already in use"

**Solution**: Change port in `.env`:

```env
DB_PORT=5433
```

Then restart:

```bash
docker compose down
docker compose up -d
```

### Error: "Missing CSV files"

**Solution**: Ensure CSV files exist in `cleaned_data/` directory:

```bash
ls -la cleaned_data/
```

---

## ✅ Success Checklist

- [ ] Docker running: `docker compose ps`
- [ ] Python installed: `python --version`
- [ ] Dependencies installed: `pip list | grep pandas`
- [ ] Health check passed: `python healthcheck.py`
- [ ] ETL executed: `python -m etl_pipeline.main`
- [ ] Logs generated: `cat etl_pipeline/execution_logs/etl.log`
- [ ] Data loaded: `docker exec shoporder_postgres_16 psql -U postgres -d shoporder -c "SELECT COUNT(*) FROM stg_contact;"`

---

## 📞 Quick Reference

| Command                             | Purpose                    |
| ----------------------------------- | -------------------------- |
| `docker compose up -d`              | Start PostgreSQL container |
| `docker compose down`               | Stop container             |
| `docker compose ps`                 | Show container status      |
| `docker compose logs -f`            | View container logs        |
| `python healthcheck.py`             | Verify system readiness    |
| `python -m etl_pipeline.main`       | Run ETL pipeline           |
| `start_etl.bat` or `./start_etl.sh` | Automated startup          |

---

## 🎓 Next Steps

1. Run the ETL once to verify it works
2. Check the output logs and reports
3. Query the database to verify data loaded
4. Modify configuration as needed for your environment
5. Schedule periodic ETL runs as needed

---

**Ready to run? Start with**:

```bash
docker compose up -d && sleep 15 && python healthcheck.py && python -m etl_pipeline.main
```

---

**Generated**: 2026-06-19  
**Database**: PostgreSQL 16  
**Status**: Production Ready ✅
