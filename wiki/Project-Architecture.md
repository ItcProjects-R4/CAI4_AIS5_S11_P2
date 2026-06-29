# Project Architecture

This page explains every layer of the Customer Data ETL system in detail, so you can understand how data moves from raw source files to a clean, query-ready PostgreSQL database.

---

## Architecture Overview

The system follows a classic **Medallion Architecture** pattern:

```
[Raw Sources]  -->  [Bronze: raw/]  -->  [Silver: Python ETL]  -->  [Gold: clean/ + PostgreSQL]
```

| Layer | Name | Description |
|---|---|---|
| Raw | Bronze | Unmodified source files land in `data/raw/` |
| Transform | Silver | Python ETL pipeline cleans, validates, and normalizes |
| Load | Gold | Clean CSV in `data/clean/` and rows in PostgreSQL tables |

---

## Full Architecture Diagram

```
data/raw/                      Python ETL Pipeline               data/clean/
contacts.csv            ┌─────────────────────────┐        contacts_clean.csv
customers.csv           │ 1. Extract (read CSVs)  │        customers_clean.csv
products.csv            │ 2. Transform (clean)    │        products_clean.csv
sales_orders.csv        │ 3. Validate (quality)   │        sales_orders_clean.csv
order_lines.csv         │ 4. Load (PostgreSQL)    │        order_lines_clean.csv
etl_batch.csv           │ 5. Reconcile (verify)   │        etl_batch_clean.csv
                        └───────────┬─────────────┘
                                    │
                                    v
                              PostgreSQL crm_db
                              ├── stg_contact (staging)
                              ├── stg_customer
                              ├── stg_product
                              ├── stg_sales_order
                              ├── stg_order_line
                              ├── contact (gold)
                              ├── customer
                              ├── product
                              ├── sales_order
                              ├── order_line
                              └── etl_batch
```

---

## Data Sources

The pipeline reads **six CSV files** from `data/raw/`, each representing one entity. These files are exported from the source CRM system.

| File | Contents |
|---|---|
| `contacts.csv` | Contact records with email, name, phone, address |
| `customers.csv` | Customer accounts with segment, status |
| `products.csv` | Product catalog with SKU, category, price |
| `sales_orders.csv` | Order headers with dates, status, totals |
| `order_lines.csv` | Line items with quantity, unit price |
| `etl_batch.csv` | Pipeline run metadata |

All files share a consistent header row and UTF-8 encoding. Full schema details on the [Data Sources](./Data-Sources.md) page.

---

## Extraction Layer

The extraction layer reads each CSV file from `data/raw/` into a pandas DataFrame. No transformations happen here — data is read as-is.

**Module:** `etl/extract.py`

| Source | Function | Description |
|---|---|---|
| `contacts.csv` | `extract_contacts()` | Reads CSV, validates headers |
| `customers.csv` | `extract_customers()` | Reads CSV, validates headers |
| `products.csv` | `extract_products()` | Reads CSV, validates headers |
| `sales_orders.csv` | `extract_sales_orders()` | Reads CSV, validates headers |
| `order_lines.csv` | `extract_order_lines()` | Reads CSV, validates headers |
| `etl_batch.csv` | `extract_etl_batch()` | Reads CSV, validates headers |

---

## Transformation Layer

The transformation layer cleans and normalises each entity independently. It applies a consistent set of rules across all fields.

**Module:** `etl/transform.py`

### Per-Entity Transformations

| Entity | Key Transform Functions |
|---|---|
| contacts | Clean email (lowercase, trim), title-case name, clean phone, canonicalise department |
| customers | Parse dates, canonicalise segment values |
| products | Validate SKU format, clean numeric prices |
| sales_orders | Parse order dates, canonicalise status and currency |
| order_lines | Clean numeric quantity and unit price |
| etl_batch | Parse timestamps, validate status |

### Business Rules Applied

- `email` → lowercased and trimmed
- `full_name` → title-cased and trimmed
- `phone` → digits/dashes only
- `department` → canonicalised via lookup table
- `country` → title-cased
- `segment` → canonicalised (`b2b`, `b2c`, `corporate`, `retail`)
- `order_status` → canonicalised (`pending`, `completed`, `cancelled`, `shipped`)
- `currency` → validated (`USD`, `EGP`)
- `list_price`, `order_total`, `quantity`, `unit_price` → parsed to numeric

---

## Validation Layer

After transformation, each entity is validated for data quality. Records that fail validation are quarantined rather than rejected outright.

**Module:** `etl/validate.py`

| Check | Scope | Action on Failure |
|---|---|---|
| Primary key uniqueness | All tables | Quarantine duplicates |
| Required field nulls | All tables | Quarantine rows with missing PKs |
| Email uniqueness | contacts | Quarantine duplicates (cascade FK children) |
| SKU uniqueness | products | Quarantine duplicates (cascade FK children) |
| Email format | contacts | Quarantine malformed emails |
| FK referential integrity | customers, sales_orders, order_lines | Quarantine orphan records |
| Date parseability | sales_orders, customers | Quarantine unparseable dates |
| Numeric range | products, order_lines | Quarantine negative prices/quantities |

### Output Files

| Directory | Contents |
|---|---|
| `data/clean/` | Valid records, one CSV per entity |
| `data/quarantine/` | Recoverable records with issues |
| `data/rejected/` | Unrecoverable records |

---

## Loading Layer

The load layer upserts clean records into PostgreSQL using a staging → gold table pattern.

**Module:** `etl/load.py`

### Staging Tables (`stg_*`)

Each entity has a corresponding staging table. Before each load:

1. Staging tables are truncated
2. Clean CSVs are bulk-copied into staging tables
3. Stored procedures move data from staging to gold tables using upsert logic

### Gold Tables

Gold tables hold the canonical, clean record set. The upsert procedure (`04_load_procedures.sql`) handles:

- **INSERT** for new records
- **UPDATE** for existing records (matched on PK)
- **DELETE** for records with violating unique keys (email duplicates, SKU duplicates) before re-inserting the valid version

### Execution Order

1. `contact` (no FK dependencies)
2. `product` (no FK dependencies)
3. `customer` (FK → contact)
4. `sales_order` (FK → customer)
5. `order_line` (FK → sales_order + product)

---

## Reconcile Layer

After loading, the reconcile layer verifies that the database row counts match the clean CSV output.

**Module:** `etl/reconcile.py`

| Check | Query |
|---|---|
| Row count match | `SELECT COUNT(*) FROM gold_table` vs `len(clean_df)` |
| FK integrity | `SELECT * FROM child WHERE parent_id NOT IN (SELECT id FROM parent)` |

---

## Data Storage

| Location | Type | Contents |
|---|---|---|
| `data/raw/` | Local filesystem | Unmodified source files — never changed by the pipeline |
| `data/clean/` | Local filesystem | Validated output CSV files |
| `data/quarantine/` | Local filesystem | Records with recoverable issues |
| `data/rejected/` | Local filesystem | Unrecoverable records |
| `crm_db` | PostgreSQL | Gold tables with upserted records |

---

## Orchestration

The pipeline is orchestrated by the Python script `etl/main.py`, which calls each module in sequence:

```
extract() → transform() → validate() → load() → reconcile()
```

### Running the Pipeline

```bash
# Full run (CSV + PostgreSQL)
python -m etl

# CSV only (skip DB load)
python -m etl --skip-db
```

### Monitoring

- Console output during each run
- Log files written to `etl/logs/`
- Run metadata recorded in the `etl_batch` table

---

## Logging and Monitoring

### Console Output

Each pipeline step prints progress, row counts, and any warnings to stdout.

### Log Files

Logs are written to `etl/logs/` with a timestamped filename. Only the most recent log is retained.

### Audit Table

Each pipeline run is recorded in the `etl_batch` table with:
- `etl_batch_id` — unique run identifier
- `pipeline_run_id` — run reference
- `started_at` / `ended_at` — timestamps
- `status` — success / failure
- `notes` — summary of warnings and errors

### Data Quality Monitoring

After each run, the validation queries in `scripts/sql/scripts/05_validation_queries.sql` should be executed to verify:
- Row counts match expectations
- No null key fields exist
- No duplicates were introduced

See the [Data Quality Definitions](./Data-Quality-Definitions.md) page for the full tier definitions.
