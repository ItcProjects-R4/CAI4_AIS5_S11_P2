# ETL Pipeline

This page explains how the Python ETL pipeline works end-to-end -- from reading raw CSV source files to writing clean data into PostgreSQL.

---

## Pipeline Overview

The pipeline is a Python module (`etl/`) run from the command line. It executes five sequential stages:

```
python -m etl

  1. EXTRACT    Reads data/raw/*.csv
  2. TRANSFORM  Cleans and normalises all fields
  3. VALIDATE   Quality checks, quarantine bad records
  4. LOAD       Upserts into PostgreSQL (staging → gold)
  5. RECONCILE  Verifies DB counts match clean CSVs
```

Each stage prints a summary to the console. If any stage fails critically, the pipeline halts and logs the error.

---

## Stage 1: Extract

**Module:** `etl/extract.py`

Reads each of the six CSV files from `data/raw/` into a pandas DataFrame. Validates that required columns exist and the file is not empty.

| Input File | Output Variable |
|---|---|
| `data/raw/contacts.csv` | `df_contacts` |
| `data/raw/customers.csv` | `df_customers` |
| `data/raw/products.csv` | `df_products` |
| `data/raw/sales_orders.csv` | `df_sales_orders` |
| `data/raw/order_lines.csv` | `df_order_lines` |
| `data/raw/etl_batch.csv` | `df_etl_batch` |

If a file is missing or unreadable, the pipeline logs an error and exits.

---

## Stage 2: Transform

**Module:** `etl/transform.py`

Applies cleaning and normalisation rules to each entity independently.

### Common Rules

| Rule | Applies To |
|---|---|
| Strip whitespace, convert NaN → NULL | All string fields |
| Lowercase and trim | `email` |
| Title-case | `full_name` |
| Digits/dashes only | `phone` |
| Canonicalise via lookup | `department`, `segment`, `order_status` |
| Parse dates to ISO | `created_at`, `updated_at`, `order_date`, `customer_since` |
| Parse numeric strings to float | `list_price`, `order_total`, `quantity`, `unit_price` |

### Per-Entity Transformations

| Entity | Specific Logic |
|---|---|
| contacts | Clean email, title-case name, clean phone, canonicalise department |
| customers | Parse `customer_since`, canonicalise segment |
| products | Clean SKU, parse price, canonicalise category |
| sales_orders | Parse order date, canonicalise status & currency |
| order_lines | Clean numeric quantity & unit price |
| etl_batch | Parse timestamps |

Full rule details on the [Transformation Rules](./Transformation-Rules.md) page.

---

## Stage 3: Validate

**Module:** `etl/validate.py`

Validates data quality and routes records to clean, quarantine, or rejected output.

### Validation Checks

| Check | Implementation |
|---|---|
| PK uniqueness | Drop duplicates by primary key |
| Required field nulls | Drop rows where PK is null |
| Email uniqueness | `groupby("email")` → keep first, quarantine rest + cascade FK children |
| SKU uniqueness | `groupby("sku")` → keep first, quarantine rest + cascade FK children |
| Email format | `@` and domain presence check |
| FK referential integrity | Verify child FK exists in parent clean set |
| Date parseability | `pd.to_datetime(..., errors="coerce")` |
| Numeric range | `quantity > 0`, `unit_price >= 0` |

### Routing

| Outcome | Directory | Description |
|---|---|---|
| Clean | `data/clean/` | Passes all checks |
| Quarantine | `data/quarantine/` | Has issues but may be recoverable (email/SKU duplicates, FK orphans) |
| Rejected | `data/rejected/` | Missing PKs or corrupt data |

---

## Stage 4: Load

**Module:** `etl/load.py`

Loads clean records into PostgreSQL using a staging → gold pattern.

### Step 1: Truncate Staging

```sql
TRUNCATE TABLE stg_contact, stg_customer, stg_product, stg_sales_order, stg_order_line;
```

### Step 2: Bulk Copy into Staging

Clean CSVs are loaded into staging tables using `COPY ... FROM STDIN WITH CSV`.

### Step 3: Upsert Staging → Gold

Stored procedures (defined in `04_load_procedures.sql`) move data from staging to gold tables:

- **INSERT** new records where PK does not exist in gold
- **UPDATE** existing records where PK matches
- **DELETE** conflicting records before re-inserting (for email/SKU uniqueness constraints)

### Load Order

```
contact → customer → product → sales_order → order_line (respecting FK dependencies)
```

---

## Stage 5: Reconcile

**Module:** `etl/reconcile.py`

Verifies that the number of rows in each gold table matches the number of rows in the corresponding clean CSV.

```python
db_count = "SELECT COUNT(*) FROM contact"
csv_count = len(clean_contacts_df)
assert db_count == csv_count, "Row count mismatch"
```

If counts do not match, the pipeline logs a warning but does not fail (the mismatch is recorded in `etl_batch.notes`).

---

## Running the Pipeline

### Prerequisites

- Python 3.10+
- PostgreSQL with `crm_db` created and tables loaded
- Six CSV files in `data/raw/`

### Full Run

```bash
source venv/bin/activate
python -m etl
```

### CSV-Only Run (Skip DB)

```bash
python -m etl --skip-db
```

Use `--skip-db` when you only want to test extraction, transformation, and validation without connecting to PostgreSQL.

### Log Files

Each run writes a timestamped log file to `etl/logs/`. Only the most recent log is retained.

---

## After the Pipeline Runs

1. Check the console output or log for any warnings or errors
2. Verify output files in `data/clean/` (six CSV files)
3. Check `data/quarantine/` and `data/rejected/` for problem records
4. Run validation queries from `scripts/sql/scripts/05_validation_queries.sql` in PostgreSQL
5. Record run results in the related GitHub issue or pull request notes

---

## Common Issues

| Problem | Likely Cause | Solution |
|---|---|---|
| "File not found" | Missing CSV in `data/raw/` | Place the file there and re-run |
| "Connection refused" | PostgreSQL not running or wrong port | Check `psql` connection and verify config |
| "Table does not exist" | SQL scripts not run | Run `scripts/sql/scripts/0*.sql` in order |
| "FK violation" | Orphan records in clean data | Quarantined automatically by validate stage |
