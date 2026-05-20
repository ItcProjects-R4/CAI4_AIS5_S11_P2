# Transformation Rules

> This page documents every transformation rule applied during the Silver layer processing (Phase 2). These rules are implemented in [`scripts/python/transform.py`](../scripts/python/transform.py) and [`scripts/python/transform_itc.py`](../scripts/python/transform_itc.py).

---

## Null Handling Rules

Every field is classified as either **reject-on-null** (NOT NULL in schema — row is rejected if missing) or **null-allowed** (nullable column — NULL is preserved as-is).

### Contacts

| Field | Null Handling | Reason |
|---|---|---|
| `contact_id` | **Reject** | Primary key — cannot be empty |
| `email` | **Reject** | NOT NULL + UNIQUE in schema; core identity field |
| `full_name` | Allowed | Optional; many CRM records have email only |
| `phone` | Allowed | Optional; validated for format if present |
| `country` | Allowed | Optional geographic metadata |
| `address_line1` | Allowed | Optional |
| `city` | Allowed | Optional |
| `state` | Allowed | Optional |
| `postal_code` | Allowed | Optional |
| `company_name` | Allowed | Optional; B2B metadata |
| `department` | Allowed | Optional |
| `job_title` | Allowed | Optional |
| `created_at` | Auto-filled | Set to pipeline run timestamp |
| `etl_batch_id` | Auto-filled | Set to current batch UUID |

### Customers

| Field | Null Handling | Reason |
|---|---|---|
| `customer_id` | **Reject** | Primary key |
| `contact_id` | **Reject** | NOT NULL FK to `contact` table |
| `customer_since` | Allowed | Parsed to DATE if present; NULL if unparseable |
| `status` | Allowed | Freetext (`active`, `inactive`) |
| `segment` | Allowed | Freetext (`retail`, `corporate`) |

### Products

| Field | Null Handling | Reason |
|---|---|---|
| `product_id` | **Reject** | Primary key |
| `sku` | **Reject** | NOT NULL + UNIQUE in schema |
| `product_name` | **Reject** | NOT NULL business field |
| `category` | Allowed | Optional classification |
| `brand` | Allowed | Optional |
| `list_price` | Allowed | Numeric; parsed via `clean_numeric()` |
| `is_active` | Allowed | Boolean; defaults to 1 if missing |

### Sales Orders

| Field | Null Handling | Reason |
|---|---|---|
| `order_id` | **Reject** | Primary key |
| `customer_id` | **Reject** | NOT NULL FK to `customer` table |
| `order_date` | **Reject** | NOT NULL; cannot process an order without a date |
| `order_status` | Allowed | Freetext (`shipped`, `pending`, `cancelled`) |
| `currency` | Allowed | CHAR(3); set to `USD` (eg_crm) or `EGP` (ITC) |
| `order_total` | Allowed | Numeric; parsed via `clean_numeric()` |

### Order Lines

| Field | Null Handling | Reason |
|---|---|---|
| `order_line_id` | **Reject** | Primary key |
| `order_id` | **Reject** | NOT NULL FK to `sales_order` table |
| `product_id` | **Reject** | NOT NULL FK to `product` table |
| `line_number` | **Reject** | Part of composite UNIQUE constraint |
| `quantity` | **Reject** | Must be > 0 |
| `unit_price` | **Reject** | Must be >= 0 |

---

## Type Conversion Rules

### Date Parsing

**Function:** `parse_date_safe()` in `transform.py`

All date fields are parsed to ISO format `YYYY-MM-DD HH:MM:SS` (for DATETIME columns) or `YYYY-MM-DD` (for DATE columns). If parsing fails, the value becomes `NULL`.

| Input Format | Example Input | Parsed Output | Rule |
|---|---|---|---|
| ISO 8601 | `1996-07-04` | `1996-07-04 00:00:00` | Direct parse |
| ISO with time | `2016-11-13T00:00` | `2016-11-13 00:00:00` | Direct parse |
| Full timestamp | `1996-09-20 00:00:00` | `1996-09-20 00:00:00` | Direct parse |
| DD/MM/YYYY | `07/11/1996` | `1996-11-07 00:00:00` | `dayfirst=True` (Egyptian locale) |
| Excel serial date | `35319` | `1996-09-10 00:00:00` | Base `1899-12-30` + serial days |
| Garbage string | `19967--30` | `NULL` | Unparseable → rejected if required |
| Empty / NaN | `""`, `NaN` | `NULL` | Explicit null |

**Key design decision:** `dayfirst=True` is used for all fuzzy date parsing because the primary data sources are Egyptian CRM systems where `DD/MM/YYYY` is the standard format.

**Excel serial date detection:** Any pure-digit string with value > 30,000 (approximately year 1982) is treated as an Excel serial date. This prevents misinterpreting small numbers as serial dates.

### Numeric Parsing

**Function:** `clean_numeric()` in `transform.py`

All numeric fields (`list_price`, `order_total`, `quantity`, `unit_price`) are parsed to Python `float`. If parsing fails, the value becomes `NULL`.

| Input Format | Example Input | Parsed Output | Rule |
|---|---|---|---|
| Python numeric | `18.0`, `42` | `18.0`, `42.0` | Direct passthrough |
| String number | `"12"` | `12.0` | `float()` conversion |
| European comma | `14,4` | `14.4` | Replace `,` → `.` |
| Arabic decimal | `39٫00` | `39.0` | Replace `٫` (U+066B) → `.` |
| Currency prefix | `EGP 16.25` | `16.25` | Strip non-numeric chars |
| Currency symbol | `$99.99` | `99.99` | Strip non-numeric chars |
| Garbage | `abc`, `---` | `NULL` | No digits found |
| Empty / NaN | `""`, `NaN` | `NULL` | Explicit null |

**Stripping rule:** After replacing Arabic/European separators, all characters except digits (`0-9`), minus (`-`), and dot (`.`) are removed. The result is then parsed as `float()`.

### Boolean Parsing

| Input | Output | Rule |
|---|---|---|
| `True`, `true`, `1` | `1` | Schema uses TINYINT |
| `False`, `false`, `0` | `0` | Schema uses TINYINT |
| Missing / NaN | `NULL` | Nullable in schema |

### String Normalisation

All string fields pass through `strip_or_none()`:

1. If `NaN` or `None` → return `NULL`
2. `str(value).strip()` — remove leading/trailing whitespace
3. If result is empty string → return `NULL`
4. Otherwise → return trimmed string

**Note:** No case normalisation (uppercase/lowercase) is applied to preserve original data fidelity. The only exception is `source_system` which is derived programmatically (`northwind`, `dummyjson`, `itc_crm`).

---

## Deduplication Rules

### Match Key: `email` (contacts — the winning key)

**Why email wins over phone:**
- Email is NOT NULL in the schema — every contact has one
- Phone is nullable — not every contact has a phone number
- Email is globally unique by schema constraint (`UNIQUE KEY`)
- Phone has format inconsistencies across sources (with/without country code, extensions)

**Rule:** Two contact records with the same `email` (after trimming) are considered duplicates.

### Survivorship: Fewest-Nulls Wins

When duplicate contacts are found (same email), the record with the **fewest NULL fields** is kept as the survivor. This is implemented as:

```python
out["_nulls"] = out.isnull().sum(axis=1)
out = out.sort_values(["email", "_nulls"])  # sort by email, then nulls ascending
out = out.drop_duplicates(subset=["email"], keep="first")  # keep fewest-nulls
```

**Rationale:** The fewest-nulls strategy selects the most complete record regardless of source system or timestamp. This is preferred over "newest wins" because:
- Bronze data doesn't always have reliable `updated_at` timestamps
- A newer record with many NULLs is worse than an older complete record
- Source priority is implicitly handled: if Northwind and DummyJSON have the same email, the one with more populated fields wins

### Dedup Keys Per Entity

| Entity | Dedup Key | Constraint |
|---|---|---|
| **contacts** | `email` | UNIQUE KEY in schema |
| **customers** | `customer_id`, then `contact_id` | PK + UNIQUE KEY in schema |
| **products** | `sku` | UNIQUE KEY in schema |
| **sales_orders** | `order_id` | Primary key |
| **order_lines** | `(order_id, line_number)` | Composite UNIQUE |

### Cross-Source Dedup (ITC CRM)

When ITC CRM data is merged with eg_crm data, an additional dedup step runs during the merge to prevent cross-source collisions:

- **Existing data wins:** If an ITC record has the same UNIQUE key as an existing eg_crm record, the eg_crm record is kept (`keep="first"` where existing data is first in the concatenation).
- **Customers:** Both `customer_id` and `contact_id` are individually deduplicated (two separate UNIQUE constraints).

---

## DQ Severity Routing

The Bronze Simulated Messy data includes DQ metadata on each record: `dq_issue_severity` with values `low`, `med`, or `high`.

| Severity | Route | Reason |
|---|---|---|
| `low` | **Clean** | Minor cosmetic issues (casing, extra whitespace) |
| `med` | **Quarantine** | Moderate issues (field swaps, encoding problems) |
| `high` | **Quarantine** | Serious issues (garbled data, possible corruption) |
| _(missing)_ | **Clean** | No DQ flag = no known issues |
| _(reject condition)_ | **Rejected** | Missing NOT NULL fields (overrides severity) |

**Rejection always overrides severity.** A record flagged `low` severity but missing its `email` is still rejected.

---

## FK Cascade Rules

After all entities are individually transformed, a cascading FK post-processing step ensures referential integrity across the clean CSVs:

```
contacts → customers    (customer.contact_id must exist in clean contacts)
customers → sales_orders (order.customer_id must exist in clean customers)
sales_orders → order_lines (line.order_id must exist in clean sales_orders)
products → order_lines    (line.product_id must exist in clean products)
```

**Rule:** If a parent record is quarantined, rejected, or dedup-dropped, all its child records are moved from clean to quarantine. This prevents FK violations during the Gold/Load phase.

**Scope:** Each transform script cascades only its own data. The eg_crm cascade runs in `transform.py`; the ITC cascade runs in `transform_itc.py` scoped to the ITC batch ID to avoid re-cascading existing eg_crm data.
