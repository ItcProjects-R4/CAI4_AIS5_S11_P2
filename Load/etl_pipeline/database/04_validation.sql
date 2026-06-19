-- Validation queries for PostgreSQL
-- Row counts for all staging tables
SELECT 'stg_etl_batch' AS table_name, COUNT(*) AS row_count
FROM stg_etl_batch;

SELECT 'stg_contact' AS table_name, COUNT(*) AS row_count
FROM stg_contact;

SELECT 'stg_customer' AS table_name, COUNT(*) AS row_count
FROM stg_customer;

SELECT 'stg_product' AS table_name, COUNT(*) AS row_count
FROM stg_product;

SELECT 'stg_sales_order' AS table_name, COUNT(*) AS row_count
FROM stg_sales_order;

SELECT 'stg_order_line' AS table_name, COUNT(*) AS row_count
FROM stg_order_line;

-- Validation: NULL checks on ID columns
SELECT 'stg_etl_batch' AS table_name, COUNT(*) AS null_id_count
FROM stg_etl_batch
WHERE
    etl_batch_id IS NULL;

SELECT 'stg_contact' AS table_name, COUNT(*) AS null_id_count
FROM stg_contact
WHERE
    contact_id IS NULL;

SELECT 'stg_customer' AS table_name, COUNT(*) AS null_id_count
FROM stg_customer
WHERE
    customer_id IS NULL;

SELECT 'stg_product' AS table_name, COUNT(*) AS null_id_count
FROM stg_product
WHERE
    product_id IS NULL;

SELECT 'stg_sales_order' AS table_name, COUNT(*) AS null_id_count
FROM stg_sales_order
WHERE
    order_id IS NULL;

SELECT 'stg_order_line' AS table_name, COUNT(*) AS null_id_count
FROM stg_order_line
WHERE
    order_line_id IS NULL;

order_line_id IS NULL;

-- Validation: Duplicate key detection (by natural/staging id columns)
SELECT contact_id, COUNT(*) c
FROM stg_contact
GROUP BY
    contact_id
HAVING
    c > 1;

SELECT customer_id, COUNT(*) c
FROM stg_customer
GROUP BY
    customer_id
HAVING
    c > 1;

SELECT product_id, COUNT(*) c
FROM stg_product
GROUP BY
    product_id
HAVING
    c > 1;

SELECT order_id, COUNT(*) c
FROM stg_sales_order
GROUP BY
    order_id
HAVING
    c > 1;

SELECT order_line_id, COUNT(*) c
FROM stg_order_line
GROUP BY
    order_line_id
HAVING
    c > 1;

-- Validation: Basic aggregations for numerical fields
SELECT
    'stg_product' AS table_name,
    MIN(list_price) AS min_price,
    MAX(list_price) AS max_price,
    AVG(list_price) AS avg_price
FROM stg_product;

SELECT
    'stg_sales_order' AS table_name,
    MIN(order_total) AS min_total,
    MAX(order_total) AS max_total,
    AVG(order_total) AS avg_total
FROM stg_sales_order;