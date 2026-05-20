# Phase 2: Transformation (T Phase)

## 2.1 Silver Output Contract

**`etl_batch`**
* Row meaning (grain): One pipeline execution run
* Primary key: `etl_batch_id`
* Required fields: `etl_batch_id`

**`contacts`**
* Row meaning (grain): One unique individual person
* Primary key: `contact_id`
* Required fields: `contact_id`, `email`, `etl_batch_id`

**`customers`**
* Row meaning (grain): One unique customer account linked to a contact
* Primary key: `customer_id`
* Required fields: `customer_id`, `contact_id`, `etl_batch_id`

**`products`**
* Row meaning (grain): One unique product identified by its SKU
* Primary key: `product_id`
* Required fields: `product_id`, `sku`, `product_name`, `etl_batch_id`

**`sales_orders`**
* Row meaning (grain): One distinct sales order transaction made by a customer
* Primary key: `order_id`
* Required fields: `order_id`, `customer_id`, `order_date`, `etl_batch_id`

**`order_lines`**
* Row meaning (grain): One distinct line item representing a product within a sales order
* Primary key: `order_line_id`
* Required fields: `order_line_id`, `order_id`, `product_id`, `line_number`, `quantity`, `unit_price`

---

## 2.2 Transformation Logic

### Null Handling Rules

| Field Group | Nulls Allowed | Nulls Cause Rejection |
|---|---|---|
| Contact identity | `full_name`, `phone`, `country`, `address_*`, `company_name`, `department`, `job_title` | `email` (NOT NULL in schema) |
| Customer identity | `customer_since`, `status`, `segment` | `contact_id` (FK required) |
| Product identity | `category`, `brand`, `list_price` | `sku`, `product_name` |
| Sales order fields | `order_status`, `currency`, `order_total` | `customer_id` (FK), `order_date` |
| Order line fields | (none) | `order_id`, `product_id`, `line_number`, `quantity`, `unit_price` |

### Type Conversion Rules

**Date parsing (multiple formats -> ISO or NULL)**
* ISO 8601: `1996-07-04` -> `1996-07-04 00:00:00`
* DD/MM/YYYY: `07/11/1996` -> `1996-11-07 00:00:00` (dayfirst=True)
* Partial timestamps: `1996-09-20 00:00:00`, `2016-11-13T00:00` -> normalized
* Excel serial dates: `35319` -> `1996-09-10 00:00:00` (base 1899-12-30)
* Unparseable garbage: `19967--30`, `1996-0-902` -> NULL (rejected)

**Numeric parsing (commas, Arabic numerals -> decimal/int or NULL)**
* Arabic decimal: `39٫00` -> `39.0`
* European comma: `14,4` -> `14.4`
* Currency prefix: `EGP 16.25` -> `16.25`
* String int: `"12"` -> `12`

### Deduplication Rules

* **Match key:** `email` (for contacts), `customer_id` (for customers), `sku` (for products), `order_id` (for sales_orders), `(order_id, line_number)` (for order_lines)
* **Survivorship:** Record with fewest NULL fields wins (ties broken by source order)

---

## 2.3 Rejected vs Quarantine

### Rejected (dropped, cannot be repaired automatically)
* Missing critical NOT NULL business keys
* Example: contact with `email = NULL`, sales order with unparseable `order_date`
* Output: `data/rejected/<entity>.csv`

### Quarantine (kept for review, not loaded to Gold)
* Record has valid identity but data quality issues flagged as `high` or `med` severity
* **FK cascade quarantine:** child record whose parent was quarantined/rejected/dedup-dropped
* Example: customer whose contact was deduplicated away, order whose customer was quarantined
* Output: `data/quarantine/<entity>.csv`

### Clean (ready for Gold load)
* Passes all NOT NULL checks, severity is `low` or no issues
* **Passes FK integrity** - every FK references a row that exists in the clean split of its parent table
* Output: `data/clean/<entity>.csv`

---

## 2.4 Pipeline Flow (as implemented)

### Step Order

1. `scripts/python/extract.py` -> writes Bronze Clean to `data/raw/bronze_clean/`
2. `.simulation/make_messy.py` -> writes Bronze Simulated Messy to `data/raw/bronze_simulated_messy/eg_crm/` + messiness report
3. `scripts/python/transform.py` -> reads Bronze Messy, produces Silver outputs:
   * **Step A:** Per-entity transformation (clean/validate/dedup each entity independently)
   * **Step B:** FK cascade post-processing (re-route orphaned children to quarantine)
   * Final output: `data/clean/`, `data/quarantine/`, `data/rejected/`
4. Load step (TBD) -> inserts `data/clean/*.csv` into MySQL `shopOrder` database

### Entry Point

```
python scripts/python/main.py
```

### Output Summary (Last Run)

| Entity | Clean | Quarantine | Rejected |
|---|---|---|---|
| contacts | 210 | 62 | 1 |
| customers | 200 | 99 | 0 |
| products | 257 | 13 | 0 |
| sales_orders | 531 | 481 | 26 |
| order_lines | 1380 | 1575 | 0 |

### Data Quality Audit (All Pass)

| Check | Result |
|---|---|
| NOT NULL constraints | 0 violations |
| UNIQUE KEY constraints | 0 violations |
| FK INTEGRITY (all 4 FK relationships) | 0 orphans |
| CHECK constraints (price >= 0, qty > 0) | 0 violations |
| VARCHAR/CHAR length limits | 0 violations |
