# Run Guide

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.13+ | Tested on 3.14 |
| PostgreSQL | 16+ | Tested on 18 |
| `psql` | — | CLI client for DB setup |
| `git` | — | Version control |

---

## 1. Clone & Environment

```bash
git clone https://github.com/ItcProjects-R4/CAI4_AIS5_S11_P2.git
cd CAI4_AIS5_S11_P2

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` only needs `psycopg2-binary` — everything else is stdlib.

---

## 2. Data

Place raw CSV files in `data/raw/`. The pipeline expects these files:

| File | Contents |
|------|----------|
| `etl_batch.csv` | Batch metadata |
| `contacts.csv` | Contact records |
| `customers.csv` | Customer records |
| `products.csv` | Product catalog |
| `sales_orders.csv` | Order headers |
| `order_lines.csv` | Order line items |

The repo includes sample data for all six tables.

---

## 3. Database Setup

### 3.1 Start PostgreSQL & Create Role

```bash
# Create a PostgreSQL role matching your OS username (for peer auth)
sudo -u postgres psql -c "CREATE ROLE $(whoami) LOGIN SUPERUSER;"
```

### 3.2 Create Database

```bash
createdb crm_db
```

### 3.3 Run Schema Scripts

Run these in order:

```bash
psql -U $(whoami) -d crm_db -f scripts/sql/scripts/02_create_tables.sql
psql -U $(whoami) -d crm_db -f scripts/sql/scripts/03_create_views.sql
psql -U $(whoami) -d crm_db -f scripts/sql/scripts/04_load_procedures.sql
```

---

## 4. Configuration

Edit `etl/config.py` if your PostgreSQL setup differs from the defaults:

```python
DB_CONFIG = {
    "host": "/var/run/postgresql",   # Unix socket path
    "port": 5433,                     # Your PostgreSQL port
    "database": "crm_db",
    "user": "alih",                   # Your OS/PG username
    "password": "",
}
```

On standard installations use `host="localhost"` and `port=5432`.

---

## 5. Run the Pipeline

```bash
source venv/bin/activate

# CSV-only run (no DB) — for testing transforms
python -m etl --skip-db

# Full pipeline (extract → transform → validate → load → reconcile)
python -m etl
```

When running full pipeline, you'll be prompted for DB credentials. Press Enter to accept defaults.

---

## 6. Pipeline Stages

```
data/raw/  ──►  Extract  ──►  Transform  ──►  Validate  ──►  Load  ──►  Reconcile
                          │               │                              │
                          ▼               ▼                              ▼
                    data/clean/      data/quarantine/               Report with
                    data/rejected/                                  row counts
```

| Stage | Description | Output |
|-------|-------------|--------|
| **Extract** | Reads CSVs from `data/raw/` | In-memory dict of rows |
| **Transform** | Cleans, normalises, repairs | `data/clean/`, `data/quarantine/`, `data/rejected/` |
| **Validate** | PK uniqueness, required fields, FK integrity, email/SKU uniqueness | Quarantined rows appended to `data/quarantine/` |
| **Load** | Truncates staging, bulk-loads clean CSVs, upserts into gold | PostgreSQL gold tables |
| **Reconcile** | Verifies no rows lost, DB staging == gold counts | Console report |

### Run Logs

Each run creates a timestamped directory under `etl/logs/` with per-component log files and a `pipeline_summary.json`.

---

## 7. Verify Results

```sql
-- Check row counts
SELECT 'etl_batch' AS tbl, COUNT(*) FROM etl_batch
UNION ALL
SELECT 'contact', COUNT(*) FROM contact
UNION ALL
SELECT 'customer', COUNT(*) FROM customer
UNION ALL
SELECT 'product', COUNT(*) FROM product
UNION ALL
SELECT 'sales_order', COUNT(*) FROM sales_order
UNION ALL
SELECT 'order_line', COUNT(*) FROM order_line;
```

Expected counts after a clean run with the sample data:

| Table | Rows |
|-------|------|
| `etl_batch` | 2 |
| `contact` | 1,586 |
| `customer` | 1,539 |
| `product` | 757 |
| `sales_order` | 2,630 |
| `order_line` | 3,257 |

Or run the validation queries:

```bash
psql -U $(whoami) -d crm_db -f scripts/sql/scripts/05_validation_queries.sql
```

---

## 8. Quick Start (TL;DR)

```bash
git clone https://github.com/ItcProjects-R4/CAI4_AIS5_S11_P2.git
cd CAI4_AIS5_S11_P2
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# DB setup (one-time)
sudo -u postgres psql -c "CREATE ROLE $(whoami) LOGIN SUPERUSER;"
createdb crm_db
for f in scripts/sql/scripts/0*.sql; do psql -U $(whoami) -d crm_db -f "$f"; done

# Run
python -m etl
```

---

## 9. Troubleshooting

| Problem | Cause / Fix |
|---------|-------------|
| `Peer authentication failed` | PG role doesn't match OS user. Create role: `CREATE ROLE $(whoami) LOGIN;` |
| `relation "stg_contact" does not exist` | Schema scripts not run. Run `02_create_tables.sql` first |
| `duplicate key value violates unique constraint "uq_contact_email"` | Pipeline now handles this — run again with latest code |
| `connection refused` | PostgreSQL not running or wrong port. Check `pg_isready` and `DB_CONFIG` port |
| `ModuleNotFoundError: No module named 'etl'` | Run from project root: `python -m etl` |
| `FATAL: database "crm_db" does not exist` | Run `createdb crm_db` first |
