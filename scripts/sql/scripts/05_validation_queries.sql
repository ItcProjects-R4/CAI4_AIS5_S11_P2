-- =====================================================
-- 05_validation_queries.sql
-- PostgreSQL Gold Layer Validation (read-only)
--
-- Built from actual results run against this database. Findings:
--   * Staging counts == Gold counts exactly (1613/1602/757/2743/3592).
--   * FK orphans are structurally impossible here because Gold tables
--     enforce FOREIGN KEY constraints -- these checks should ALWAYS
--     return 0 and exist purely as a regression trip-wire (e.g. if
--     someone ever loads with constraints disabled).
--   * sales_order.order_total is NOT reliable: a meaningful number of
--     orders have order_total = 0.0000 while their order_line rows
--     sum to a real, nonzero amount. Treat SUM(order_line) as the
--     canonical revenue figure, not sales_order.order_total.
--   * 15 orders currently have zero order_line rows (not an FK
--     violation -- just orders with no line data loaded).
--   * 20+ orders have order_date issues: some are in the future,
--     some predate the customer's own customer_since date.
--
-- Sections:
--   1. Row count reconciliation (staging vs gold)
--   2. Referential integrity (should always be 0)
--   3. CHECK-constraint-equivalent sanity (should always be 0)
--   4. Duplicate business key checks (should always be 0)
--   5. Known data-quality findings (expected to be nonzero -- track,
--      don't "fix" by editing this file)
--   6. Categorical value inventory (informational, eyeball check)
--   7. One-shot summary dashboard
-- =====================================================


-- =====================================================
-- 1. Row count reconciliation: staging vs gold
-- Expect every pair to match exactly.
-- =====================================================
SELECT 'contact'     AS table_name, (SELECT COUNT(*) FROM stg_contact)     AS staging_count, (SELECT COUNT(*) FROM contact)     AS gold_count
UNION ALL
SELECT 'customer',     (SELECT COUNT(*) FROM stg_customer),    (SELECT COUNT(*) FROM customer)
UNION ALL
SELECT 'product',      (SELECT COUNT(*) FROM stg_product),     (SELECT COUNT(*) FROM product)
UNION ALL
SELECT 'sales_order',  (SELECT COUNT(*) FROM stg_sales_order), (SELECT COUNT(*) FROM sales_order)
UNION ALL
SELECT 'order_line',   (SELECT COUNT(*) FROM stg_order_line),  (SELECT COUNT(*) FROM order_line)
UNION ALL
SELECT 'etl_batch',    (SELECT COUNT(*) FROM stg_etl_batch),   (SELECT COUNT(*) FROM etl_batch);


-- =====================================================
-- 2. Referential integrity in Gold
-- These are guaranteed 0 by FOREIGN KEY constraints on the tables.
-- Kept as an explicit trip-wire, not because orphans are expected.
-- =====================================================
SELECT 'customer->contact orphans' AS check_name,
       COUNT(*) AS issue_count
FROM customer c
LEFT JOIN contact ct ON ct.contact_id = c.contact_id
WHERE ct.contact_id IS NULL

UNION ALL
SELECT 'sales_order->customer orphans',
       COUNT(*)
FROM sales_order so
LEFT JOIN customer c ON c.customer_id = so.customer_id
WHERE c.customer_id IS NULL

UNION ALL
SELECT 'order_line->sales_order orphans',
       COUNT(*)
FROM order_line ol
LEFT JOIN sales_order so ON so.order_id = ol.order_id
WHERE so.order_id IS NULL

UNION ALL
SELECT 'order_line->product orphans',
       COUNT(*)
FROM order_line ol
LEFT JOIN product p ON p.product_id = ol.product_id
WHERE p.product_id IS NULL;


-- =====================================================
-- 3. CHECK-constraint-equivalent sanity
-- Already enforced by table CHECK constraints; verifies no rows
-- ever bypassed them (e.g. via a bulk load with constraints off).
-- Expect all 0.
-- =====================================================
SELECT 'order_line.quantity <= 0' AS check_name, COUNT(*) AS issue_count FROM order_line WHERE quantity <= 0
UNION ALL
SELECT 'order_line.unit_price < 0',            COUNT(*) FROM order_line  WHERE unit_price < 0
UNION ALL
SELECT 'product.list_price < 0',               COUNT(*) FROM product    WHERE list_price < 0
UNION ALL
SELECT 'sales_order.order_total < 0',          COUNT(*) FROM sales_order WHERE order_total < 0
UNION ALL
SELECT 'contact.email malformed',              COUNT(*) FROM contact    WHERE email NOT LIKE '%_@_%._%';


-- =====================================================
-- 4. Duplicate business key checks (Gold)
-- PK + UNIQUE constraints already guarantee these are 0; kept as an
-- explicit business-key-level check independent of constraint names.
-- =====================================================
SELECT 'duplicate contact.email' AS check_name, COUNT(*) AS issue_count
FROM (SELECT email FROM contact GROUP BY email HAVING COUNT(*) > 1) d

UNION ALL
SELECT 'duplicate customer.contact_id',
       COUNT(*)
FROM (SELECT contact_id FROM customer GROUP BY contact_id HAVING COUNT(*) > 1) d

UNION ALL
SELECT 'duplicate product.sku',
       COUNT(*)
FROM (SELECT sku FROM product GROUP BY sku HAVING COUNT(*) > 1) d

UNION ALL
SELECT 'duplicate order_line (order_id, line_number)',
       COUNT(*)
FROM (SELECT order_id, line_number FROM order_line GROUP BY order_id, line_number HAVING COUNT(*) > 1) d;


-- =====================================================
-- 5. Known data-quality findings (expected to be nonzero)
-- These are real, confirmed issues in the source data -- not bugs in
-- the load. Track counts/trend over time rather than expecting 0.
-- =====================================================

-- 5a. sales_order.order_total disagrees with SUM(order_line).
-- Confirmed pattern: order_total = 0.0000 while line items sum to a
-- real amount. Report count + total dollar variance.
SELECT
    COUNT(*)                                   AS orders_with_total_mismatch,
    SUM(computed_total - stored_total)          AS total_understatement
FROM (
    SELECT
        so.order_id,
        so.order_total                          AS stored_total,
        SUM(ol.quantity * ol.unit_price)        AS computed_total
    FROM sales_order so
    JOIN order_line ol ON ol.order_id = so.order_id
    GROUP BY so.order_id, so.order_total
    HAVING ABS(so.order_total - SUM(ol.quantity * ol.unit_price)) > 0.01
) mismatched;

-- Detail rows (drop/raise the LIMIT as needed when investigating)
SELECT
    so.order_id,
    so.order_total                              AS stored_total,
    SUM(ol.quantity * ol.unit_price)            AS computed_total,
    so.order_total - SUM(ol.quantity * ol.unit_price) AS diff
FROM sales_order so
JOIN order_line ol ON ol.order_id = so.order_id
GROUP BY so.order_id, so.order_total
HAVING ABS(so.order_total - SUM(ol.quantity * ol.unit_price)) > 0.01
ORDER BY diff
LIMIT 50;

-- 5b. Orders with zero order_line rows. Confirmed: 15 currently.
SELECT COUNT(*) AS orders_with_no_lines
FROM sales_order so
LEFT JOIN order_line ol ON ol.order_id = so.order_id
WHERE ol.order_id IS NULL;

SELECT so.order_id, so.order_date, so.order_status, so.order_total
FROM sales_order so
LEFT JOIN order_line ol ON ol.order_id = so.order_id
WHERE ol.order_id IS NULL
ORDER BY so.order_date DESC;

-- 5c. order_date anomalies: future-dated orders, and orders placed
-- before the customer's own customer_since date.
SELECT
    SUM(CASE WHEN so.order_date > NOW() THEN 1 ELSE 0 END)               AS future_dated_orders,
    SUM(CASE WHEN so.order_date < c.customer_since THEN 1 ELSE 0 END)    AS orders_before_customer_since
FROM sales_order so
JOIN customer c ON c.customer_id = so.customer_id;

SELECT
    so.order_id,
    so.order_date,
    c.customer_since,
    CASE
        WHEN so.order_date > NOW() THEN 'future_dated'
        WHEN so.order_date < c.customer_since THEN 'before_customer_since'
    END AS anomaly_type
FROM sales_order so
JOIN customer c ON c.customer_id = so.customer_id
WHERE so.order_date > NOW()
   OR so.order_date < c.customer_since
ORDER BY anomaly_type, so.order_date;


-- =====================================================
-- 6. Categorical value inventory (informational)
-- Eyeball check for typos/casing drift (e.g. 'Active' vs 'active').
-- Not a pass/fail check -- just visibility into what values exist.
-- =====================================================
SELECT 'sales_order.order_status' AS column_name, order_status AS value, COUNT(*) AS row_count
FROM sales_order GROUP BY order_status
UNION ALL
SELECT 'customer.status', status, COUNT(*) FROM customer GROUP BY status
UNION ALL
SELECT 'customer.segment', segment, COUNT(*) FROM customer GROUP BY segment
UNION ALL
SELECT 'sales_order.currency', currency, COUNT(*) FROM sales_order GROUP BY currency
UNION ALL
SELECT 'product.is_active', is_active::text, COUNT(*) FROM product GROUP BY is_active
ORDER BY column_name, row_count DESC;


-- =====================================================
-- 7. One-shot summary dashboard
-- Run this alone for a quick health check. HARD checks should always
-- read 0 / PASS. SOFT checks are known findings, tracked not "fixed".
-- =====================================================
WITH hard_checks AS (
    SELECT 'orphan: customer->contact' AS check_name,
           (SELECT COUNT(*) FROM customer c LEFT JOIN contact ct ON ct.contact_id = c.contact_id WHERE ct.contact_id IS NULL) AS issue_count
    UNION ALL
    SELECT 'orphan: sales_order->customer',
           (SELECT COUNT(*) FROM sales_order so LEFT JOIN customer c ON c.customer_id = so.customer_id WHERE c.customer_id IS NULL)
    UNION ALL
    SELECT 'orphan: order_line->sales_order',
           (SELECT COUNT(*) FROM order_line ol LEFT JOIN sales_order so ON so.order_id = ol.order_id WHERE so.order_id IS NULL)
    UNION ALL
    SELECT 'orphan: order_line->product',
           (SELECT COUNT(*) FROM order_line ol LEFT JOIN product p ON p.product_id = ol.product_id WHERE p.product_id IS NULL)
    UNION ALL
    SELECT 'check: order_line.quantity <= 0',
           (SELECT COUNT(*) FROM order_line WHERE quantity <= 0)
    UNION ALL
    SELECT 'check: order_line.unit_price < 0',
           (SELECT COUNT(*) FROM order_line WHERE unit_price < 0)
    UNION ALL
    SELECT 'check: product.list_price < 0',
           (SELECT COUNT(*) FROM product WHERE list_price < 0)
    UNION ALL
    SELECT 'check: sales_order.order_total < 0',
           (SELECT COUNT(*) FROM sales_order WHERE order_total < 0)
    UNION ALL
    SELECT 'check: contact.email malformed',
           (SELECT COUNT(*) FROM contact WHERE email NOT LIKE '%_@_%._%')
    UNION ALL
    SELECT 'duplicate: contact.email',
           (SELECT COUNT(*) FROM (SELECT email FROM contact GROUP BY email HAVING COUNT(*) > 1) d)
    UNION ALL
    SELECT 'duplicate: customer.contact_id',
           (SELECT COUNT(*) FROM (SELECT contact_id FROM customer GROUP BY contact_id HAVING COUNT(*) > 1) d)
    UNION ALL
    SELECT 'duplicate: product.sku',
           (SELECT COUNT(*) FROM (SELECT sku FROM product GROUP BY sku HAVING COUNT(*) > 1) d)
    UNION ALL
    SELECT 'duplicate: order_line (order_id, line_number)',
           (SELECT COUNT(*) FROM (SELECT order_id, line_number FROM order_line GROUP BY order_id, line_number HAVING COUNT(*) > 1) d)
),
soft_checks AS (
    SELECT 'finding: orders where order_total != SUM(order_line)' AS check_name,
           (SELECT COUNT(*) FROM (
               SELECT so.order_id
               FROM sales_order so
               JOIN order_line ol ON ol.order_id = so.order_id
               GROUP BY so.order_id, so.order_total
               HAVING ABS(so.order_total - SUM(ol.quantity * ol.unit_price)) > 0.01
           ) m) AS issue_count
    UNION ALL
    SELECT 'finding: orders with zero order_line rows',
           (SELECT COUNT(*) FROM sales_order so LEFT JOIN order_line ol ON ol.order_id = so.order_id WHERE ol.order_id IS NULL)
    UNION ALL
    SELECT 'finding: future-dated orders',
           (SELECT COUNT(*) FROM sales_order WHERE order_date > NOW())
    UNION ALL
    SELECT 'finding: orders before customer_since',
           (SELECT COUNT(*) FROM sales_order so JOIN customer c ON c.customer_id = so.customer_id WHERE so.order_date < c.customer_since)
)
SELECT 'HARD' AS severity, check_name,
       issue_count,
       CASE WHEN issue_count = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM hard_checks
UNION ALL
SELECT 'SOFT', check_name,
       issue_count,
       CASE WHEN issue_count = 0 THEN 'PASS' ELSE 'KNOWN_ISSUE' END AS status
FROM soft_checks
ORDER BY severity, status DESC, check_name;
