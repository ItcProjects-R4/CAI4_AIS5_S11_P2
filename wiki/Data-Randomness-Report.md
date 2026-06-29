# Data Randomness & Transform Changes Report

## Raw Data Randomness

### Volume

| Table | Rows | Unique PKs |
|---|---|---|
| contacts | 1,661 | 1,661 UUIDs |
| customers | 1,618 | 1,618 UUIDs |
| products | 764 | 757 SKUs (7 duplicates) |
| sales_orders | 2,770 | 2,770 UUIDs |
| order_lines | 3,663 | 3,663 UUIDs |

### Intentional Messiness

**Casing chaos** — Same values appear in mixed cases:
- `segment`: `'B2B'`, `'b2b'`, `'  B2B'`, `'\tB2B\t'`, `'B2B  '`, `'  b2b'`
- `status`: `'Active'`, `'active'`, `'ACTIVE'`, `'Active '`, `'  active'`, `'\tactive\t'`
- `order_status`: `'Pending'`, `'pending'`, `'Pendign'`, `'Pneding'`
- `currency`: `'EGP'`, `'  EGP'`, `'EGP  '`, `'\tEGP\t'`

**Whitespace contamination** — Leading/trailing spaces and tabs throughout:
- `'  retail'`, `'\tcorporate\t'`, `'  Cancelled'`, `'NorthwindCategory '`

**Typos & misspellings**:
- `category`: `'grcoeries'`, `'mobile-accessoreis'`, `'fargrances'`, `'smartpohnes'`, `'sport-saccessories'`
- `department`: `'Marekting'` (instead of `Marketing`)
- `order_status`: `'Pendign'`, `'Pneding'`, `'Cmopleted'`, `'Completde'`, `'Complteed'`, `'Comlpeted'`, `'Copmleted'`

**Date format inconsistency**:
- ISO: `'1996-07-04 00:00:00'`, `'2026-05-20'`
- US-style: `'05/20/2026'`
- Impossible dates: `'2026-13-45'` (month=13, day=45), `'2206-04-29'` (year 2206)

**Nulls / empty values**:
- 51 contacts with empty phone
- 58 customers with empty segment
- 85 orders with empty status
- 78 orders with empty currency
- 45 customers with missing `customer_since`

**Duplicate emails**: 46 duplicate email addresses (some emails shared by 2+ contacts)

**Duplicate SKUs**: 7 duplicate SKUs across products

**Currency whitespace**: `'  EGP'`, `'EGP  '`, `'\tEGP\t'`, `'  USD'`, `'USD  '`

**Price anomalies**:
- Product prices: min `0.79` to max `87,250.98`
- Order totals: min `0.00` to max `471,941.54`
- Quantities: min `1` to max `99,175`

**3 source systems**: `northwind` (561), `dummyjson` (555), `itc_crm` (545)

---

## Transform (T) Phase Changes

### extract.py — Reads raw CSVs unchanged, validates headers exist

### transform.py — Row-by-row cleaning per entity

| Rule | Implementation | Applied To |
|---|---|---|
| **Trim all fields** | `_trim()` strips whitespace, converts NaN → None | All tables |
| **Validate UUID format** | `_is_valid_uuid()` — must be 36-char hex | All PKs |
| **Validate email format** | `EMAIL_RE` regex — must contain `@` + domain | contacts |
| **Canonicalise department** | Lookup dict maps department variants → canonical form | contacts |
| **Title-case country** | `str.title()` | contacts |
| **Clean phone** | Strip non-digit/dash/paren characters | contacts |
| **Canonicalise status** | Lookup maps status variants → canonical | customers |
| **Canonicalise segment** | Lookup maps segment variants → canonical | customers |
| **Parse dates** | Try 3 ISO formats, validate result | customers, sales_orders |
| **Canonicalise category** | Lookup maps category variants → canonical | products |
| **Parse numeric prices** | `float()` conversion, reject negative → quarantine | products, sales_orders |
| **Canonicalise order_status** | Variant matching against allowed set | sales_orders |
| **Uppercase currency** | `str.upper()`, validate against allowed set | sales_orders |
| **Parse integer quantities** | `int(float())`, reject ≤ 0 | order_lines |
| **Parse line_number** | `int()`, reject ≤ 0 | order_lines |
| **Reject missing PK** | Missing `contact_id`, `email`, `sku`, `product_name`, etc. → rejected | All tables |
| **Reject invalid UUID** | Malformed PK → rejected | All tables |
| **Quarantine bad FK refs** | Orphan FK values → quarantine | customers, sales_orders, order_lines |
| **Quarantine bad dates** | Unparseable dates → quarantine | customers, sales_orders |
| **Quarantine bad segments** | Unknown segment → quarantine | customers |
| **Quarantine bad statuses** | Unknown order status → quarantine | sales_orders |
| **Quarantine bad currencies** | Unknown currency → quarantine | sales_orders |
| **Quarantine negative values** | Negative price, total, quantity → quarantine | products, sales_orders, order_lines |

### validate.py — Cross-row and cross-table integrity

| Check | Logic |
|---|---|
| **PK uniqueness** | Group by PK, keep first, quarantine rest |
| **Required fields** | Check non-null for critical columns |
| **Email uniqueness** | Group by email, keep first, quarantine rest + cascade FK chain (customer → order → line) |
| **SKU uniqueness** | Group by SKU, keep first, quarantine rest + cascade FK chain (order_line) |
| **Email format** | Regex check on all clean contacts |
| **FK integrity** | Verify every FK points to an existing parent PK across all entity pairs |
| **Routing** | Pass → `data/clean/`, Recoverable → `data/quarantine/`, Unrecoverable → `data/rejected/` |
