# Data Sources

This page describes the source data that feeds the ETL pipeline. All source files are extracted from external systems, placed in `data/raw/`, and read by the pipeline as-is.

---

## Overview

| Source | Format | Contents | Records |
|--------|--------|----------|---------|
| CRM System | CSV (UTF-8) | Customer contacts, accounts, orders | 6 tables, ~10K rows |

Data is exported from the CRM system into six CSV files. Each file represents one entity in the relational model. The files are placed in `data/raw/` before each pipeline run.

> **Rule:** Never edit files in `data/raw/`. They are the original source of truth. If there is an error in a raw file, fix it at the source system and re-export.

---

## Source Files

### Naming Convention

All files use plain names (no date suffix — each run consumes the same file names):

```
data/raw/
├── etl_batch.csv          # Pipeline run metadata
├── contacts.csv           # Contact records (customers, leads)
├── customers.csv          # Customer account records
├── products.csv           # Product catalog
├── sales_orders.csv       # Order headers
└── order_lines.csv        # Order line items
```

### File Format (All Tables)

- Encoding: UTF-8
- Delimiter: comma (`,`)
- Header: yes (first row)
- Quote character: double quote (`"`)
- Line ending: LF (Unix)

---

## Schema Details

### etl_batch

| Column | Type | Description |
|--------|------|-------------|
| `etl_batch_id` | VARCHAR(36) | Unique batch identifier |
| `pipeline_run_id` | VARCHAR(255) | Run identifier |
| `started_at` | TIMESTAMP | Batch start time |
| `ended_at` | TIMESTAMP | Batch end time |
| `status` | VARCHAR(50) | Run status |
| `notes` | TEXT | Optional notes |

### contacts

| Column | Type | Description |
|--------|------|-------------|
| `contact_id` | VARCHAR(36) | UUID primary key |
| `email` | VARCHAR(320) | Email address (unique) |
| `full_name` | VARCHAR(255) | Contact full name |
| `phone` | VARCHAR(50) | Phone number |
| `country` | VARCHAR(100) | Country name |
| `address_line1` | VARCHAR(500) | Street address |
| `city` | VARCHAR(100) | City |
| `state` | VARCHAR(100) | State / province |
| `postal_code` | VARCHAR(20) | Postal code |
| `company_name` | VARCHAR(255) | Company |
| `department` | VARCHAR(255) | Department |
| `job_title` | VARCHAR(255) | Job title |
| `attributes_json` | TEXT | Extra attributes |
| `created_at` | TIMESTAMP | Record created |
| `updated_at` | TIMESTAMP | Last updated |
| `etl_batch_id` | VARCHAR(36) | Batch FK |
| `source_system` | VARCHAR(100) | Origin system |
| `source_record_id` | VARCHAR(255) | ID in source system |

### customers

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | VARCHAR(36) | UUID primary key |
| `contact_id` | VARCHAR(36) | FK to contacts |
| `customer_since` | DATE | When they became a customer |
| `status` | VARCHAR(50) | Account status |
| `segment` | VARCHAR(100) | Customer segment |
| `created_at` | TIMESTAMP | Record created |
| `updated_at` | TIMESTAMP | Last updated |
| `etl_batch_id` | VARCHAR(36) | Batch FK |
| `source_system` | VARCHAR(100) | Origin system |
| `source_record_id` | VARCHAR(255) | ID in source system |

### products

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | VARCHAR(36) | UUID primary key |
| `sku` | VARCHAR(100) | Stock-keeping unit (unique) |
| `product_name` | VARCHAR(500) | Product name |
| `category` | VARCHAR(255) | Product category |
| `brand` | VARCHAR(255) | Brand name |
| `list_price` | NUMERIC(18,4) | Standard price |
| `is_active` | BOOLEAN | Whether active |
| `attributes_json` | TEXT | Extra attributes |
| `created_at` | TIMESTAMP | Record created |
| `updated_at` | TIMESTAMP | Last updated |
| `etl_batch_id` | VARCHAR(36) | Batch FK |
| `source_system` | VARCHAR(100) | Origin system |
| `source_record_id` | VARCHAR(255) | ID in source system |

### sales_orders

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | VARCHAR(36) | UUID primary key |
| `customer_id` | VARCHAR(36) | FK to customers |
| `order_date` | TIMESTAMP | Order date |
| `order_status` | VARCHAR(50) | Order status |
| `currency` | CHAR(3) | Currency code |
| `order_total` | NUMERIC(18,4) | Order total |
| `created_at` | TIMESTAMP | Record created |
| `updated_at` | TIMESTAMP | Last updated |
| `etl_batch_id` | VARCHAR(36) | Batch FK |
| `source_system` | VARCHAR(100) | Origin system |
| `source_record_id` | VARCHAR(255) | ID in source system |

### order_lines

| Column | Type | Description |
|--------|------|-------------|
| `order_line_id` | VARCHAR(36) | UUID primary key |
| `order_id` | VARCHAR(36) | FK to sales_orders |
| `product_id` | VARCHAR(36) | FK to products |
| `line_number` | INTEGER | Line item number |
| `quantity` | INTEGER | Quantity ordered |
| `unit_price` | NUMERIC(18,4) | Unit price |

---

## Data Quality Issues in Source

| Issue | Affected Tables | Description |
|-------|----------------|-------------|
| Missing contact_id / customer_id / order_id | All | Rows rejected by pipeline |
| Duplicate emails | contacts | Some contacts share an email — pipeline quarantines duplicates, keeping one |
| Duplicate SKUs | products | Some products share a SKU — pipeline quarantines duplicates |
| Malformed emails | contacts | Missing `@` or domain — quarantined |
| Invalid dates | sales_orders, customers | Unparseable date strings — quarantined |
| Negative prices / quantities | products, order_lines | Business rule violations — quarantined |
| Broken foreign keys | customers, sales_orders, order_lines | Referenced ID does not exist — quarantined |
| Unknown status/segment values | customers, sales_orders | Values outside allowed set — quarantined |
| Mixed casing / extra whitespace | All | Normalised during transform |

---

## Adding New Source Files

1. Export the CSV from the source system with the correct schema.
2. Place the file in `data/raw/` matching the expected file name.
3. Run the pipeline with `--skip-db` first to verify the transform works.
4. If the schema changed, update `etl/config.py` (the `FIELDS`, `RAW_FILES` dicts).

---

## Source File Checklist

- [ ] All six CSV files exist in `data/raw/`
- [ ] Each file has a header row matching the expected column names
- [ ] No columns added, removed, or renamed unexpectedly
- [ ] Encoding is UTF-8
- [ ] Run `python -m etl --skip-db` to verify before a full DB run
