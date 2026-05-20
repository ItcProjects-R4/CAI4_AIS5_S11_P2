# Phase 3: Data Quality (DQ)

## 3.1 Validation Rules

### Required Fields

All primary keys and NOT NULL fields must be present and non-empty after transformation:

| Entity | Required Fields (reject if missing) |
|---|---|
| **contacts** | `contact_id`, `email` |
| **customers** | `customer_id`, `contact_id` |
| **products** | `product_id`, `sku`, `product_name` |
| **sales_orders** | `order_id`, `customer_id`, `order_date` |
| **order_lines** | `order_line_id`, `order_id`, `product_id`, `line_number`, `quantity`, `unit_price` |

### Format Checks

**Email** (`contacts.email`):
- Must contain `@` and `.` after trimming whitespace
- Minimum length: 5 characters
- Examples that pass: `user@domain.com`, `a@b.co`
- Examples that fail: `user`, `user@`, `@.`

**Phone** (`contacts.phone`):
- Nullable (missing phone is allowed)
- If present: length must be 7-30 characters
- Allowed characters: digits (`0-9`), spaces, `+`, `-`, `(`, `)`, `.`, `x`, `#`
- Examples that pass: `+1-555-123-4567`, `(020) 1234 5678`, `555.1234x100`
- Examples that fail: `'01043268478` (leading apostrophe from Excel), `abc123`

### Uniqueness (post-dedup verification)

| Constraint | Check |
|---|---|
| `contacts.email` | No duplicate emails in clean contacts |
| `products.sku` | No duplicate SKUs in clean products |
| `order_lines.(order_id, line_number)` | No duplicate order lines in clean |

---

## 3.2 DQ Outputs

Each pipeline run produces `data/clean/dq_report.json` containing:

```json
{
  "generated_at": "2026-05-20 18:35:31",
  "entities": {
    "contacts": {
      "total_rows_processed": 1675,
      "valid_rows": 1612,
      "quarantined_rows": 62,
      "rejected_rows": 1,
      "format_issues_in_clean": 2,
      "issue_details": [...]
    }
  },
  "uniqueness_issues": [],
  "top_error_codes": [
    {"code": "INVALID_PHONE_FORMAT", "count": 2}
  ]
}
```

### Human-Readable Summary (stdout)

```
Entity              Total    Valid   Quarantine   Rejected  DQ Issues
------------------------------------------------------------------
contacts             1675     1612           62          1          2
customers            1702     1602          100          0          0
products              770      757           13          0          0
sales_orders         4038     2743         1269         26          0
order_lines          5955     3592         2363          0          0

Uniqueness violations: 0 (PASS)
```

### Error Codes Reference

| Code | Meaning | Severity |
|---|---|---|
| `MISSING_REQUIRED_ID` | Primary key or source ID is null/empty | Critical (should not appear in clean) |
| `MISSING_REQUIRED_FIELD` | NOT NULL business field is missing | Critical |
| `MISSING_REQUIRED_FK` | Foreign key reference is null | Critical |
| `INVALID_EMAIL_FORMAT` | Email fails `@` and `.` check | Warning |
| `INVALID_PHONE_FORMAT` | Phone has illegal characters or length | Warning |
| `INVALID_QUANTITY` | Quantity is null or <= 0 | Critical |
| `INVALID_PRICE` | Unit price is null or < 0 | Critical |
| `DUPLICATE_EMAIL` | Email appears more than once in clean | Critical |
| `DUPLICATE_SKU` | SKU appears more than once in clean | Critical |
| `DUPLICATE_ORDER_LINE` | (order_id, line_number) pair duplicated | Critical |

---

## 3.3 Rejected vs Quarantine

See [Data Quality Definitions](../wiki/Data-Quality-Definitions.md) for full definitions.

### Quick Reference

- **Rejected** = unrecoverable, dropped from pipeline. Missing core business keys.
- **Quarantine** = recoverable, held for review. Has identity but data quality issues or FK orphan.
- **Clean** = passes all NOT NULL, FK, and constraint checks. Ready for Gold/SQL load.
