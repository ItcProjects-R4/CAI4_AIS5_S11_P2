-- =====================================================
-- 04_load_procedures.sql
-- PostgreSQL Gold Layer Upsert Logic (Staging -> Gold)
--
-- Findings used to build this script:
--   * Staging counts already match Gold counts exactly (no data loss
--     on the prior load).
--   * Every Gold/Staging table has a single-column surrogate PK that
--     is generated consistently between staging and gold by the same
--     ETL run, so conflict targets use those PKs:
--       contact_id, customer_id, product_id, order_id, order_line_id
--   * created_at is preserved on UPDATE (only ever set on INSERT);
--     updated_at is stamped with CURRENT_TIMESTAMP whenever a row's
--     content actually changes, not just whenever it's re-processed.
--   * Each UPDATE only fires when at least one tracked column differs
--     (IS DISTINCT FROM checks), so re-running this file on unchanged
--     data is a true no-op and doesn't churn updated_at/etl_batch_id.
--   * Loads are idempotent: re-running this file is safe.
--
-- Load order respects FK dependencies:
--   etl_batch -> contact -> customer -> product -> sales_order -> order_line
-- =====================================================

BEGIN;

-- ---------------------------------------------------
-- etl_batch
-- ---------------------------------------------------
INSERT INTO etl_batch (
    etl_batch_id, pipeline_run_id, started_at, ended_at, status, notes
)
SELECT
    etl_batch_id, pipeline_run_id, started_at, ended_at, status, notes
FROM stg_etl_batch
ON CONFLICT (etl_batch_id) DO UPDATE SET
    pipeline_run_id = EXCLUDED.pipeline_run_id,
    started_at      = EXCLUDED.started_at,
    ended_at        = EXCLUDED.ended_at,
    status          = EXCLUDED.status,
    notes           = EXCLUDED.notes
WHERE
    etl_batch.pipeline_run_id IS DISTINCT FROM EXCLUDED.pipeline_run_id
    OR etl_batch.started_at   IS DISTINCT FROM EXCLUDED.started_at
    OR etl_batch.ended_at     IS DISTINCT FROM EXCLUDED.ended_at
    OR etl_batch.status       IS DISTINCT FROM EXCLUDED.status
    OR etl_batch.notes        IS DISTINCT FROM EXCLUDED.notes;

-- ---------------------------------------------------
-- contact
-- ---------------------------------------------------
INSERT INTO contact (
    contact_id, email, full_name, phone, country,
    address_line1, city, state, postal_code,
    company_name, department, job_title,
    attributes_json, created_at, updated_at,
    etl_batch_id, source_system, source_record_id
)
SELECT
    contact_id, email, full_name, phone, country,
    address_line1, city, state, postal_code,
    company_name, department, job_title,
    attributes_json, created_at, updated_at,
    etl_batch_id, source_system, source_record_id
FROM stg_contact
ON CONFLICT (contact_id) DO UPDATE SET
    email             = EXCLUDED.email,
    full_name         = EXCLUDED.full_name,
    phone             = EXCLUDED.phone,
    country           = EXCLUDED.country,
    address_line1     = EXCLUDED.address_line1,
    city              = EXCLUDED.city,
    state             = EXCLUDED.state,
    postal_code       = EXCLUDED.postal_code,
    company_name      = EXCLUDED.company_name,
    department        = EXCLUDED.department,
    job_title         = EXCLUDED.job_title,
    attributes_json   = EXCLUDED.attributes_json,
    updated_at        = CURRENT_TIMESTAMP,
    etl_batch_id      = EXCLUDED.etl_batch_id,
    source_system     = EXCLUDED.source_system,
    source_record_id  = EXCLUDED.source_record_id
WHERE
    contact.email            IS DISTINCT FROM EXCLUDED.email
    OR contact.full_name     IS DISTINCT FROM EXCLUDED.full_name
    OR contact.phone         IS DISTINCT FROM EXCLUDED.phone
    OR contact.country       IS DISTINCT FROM EXCLUDED.country
    OR contact.address_line1 IS DISTINCT FROM EXCLUDED.address_line1
    OR contact.city          IS DISTINCT FROM EXCLUDED.city
    OR contact.state         IS DISTINCT FROM EXCLUDED.state
    OR contact.postal_code   IS DISTINCT FROM EXCLUDED.postal_code
    OR contact.company_name  IS DISTINCT FROM EXCLUDED.company_name
    OR contact.department    IS DISTINCT FROM EXCLUDED.department
    OR contact.job_title     IS DISTINCT FROM EXCLUDED.job_title
    OR contact.attributes_json IS DISTINCT FROM EXCLUDED.attributes_json;

-- ---------------------------------------------------
-- customer
-- ---------------------------------------------------
INSERT INTO customer (
    customer_id, contact_id, customer_since, status, segment,
    created_at, updated_at, etl_batch_id, source_system, source_record_id
)
SELECT
    customer_id, contact_id, customer_since, status, segment,
    created_at, updated_at, etl_batch_id, source_system, source_record_id
FROM stg_customer
ON CONFLICT (customer_id) DO UPDATE SET
    contact_id        = EXCLUDED.contact_id,
    customer_since    = EXCLUDED.customer_since,
    status            = EXCLUDED.status,
    segment           = EXCLUDED.segment,
    updated_at        = CURRENT_TIMESTAMP,
    etl_batch_id      = EXCLUDED.etl_batch_id,
    source_system     = EXCLUDED.source_system,
    source_record_id  = EXCLUDED.source_record_id
WHERE
    customer.contact_id     IS DISTINCT FROM EXCLUDED.contact_id
    OR customer.customer_since IS DISTINCT FROM EXCLUDED.customer_since
    OR customer.status      IS DISTINCT FROM EXCLUDED.status
    OR customer.segment     IS DISTINCT FROM EXCLUDED.segment;

-- ---------------------------------------------------
-- product
-- ---------------------------------------------------
INSERT INTO product (
    product_id, sku, product_name, category, brand,
    list_price, is_active, attributes_json,
    created_at, updated_at, etl_batch_id, source_system, source_record_id
)
SELECT
    product_id, sku, product_name, category, brand,
    list_price, is_active, attributes_json,
    created_at, updated_at, etl_batch_id, source_system, source_record_id
FROM stg_product
ON CONFLICT (product_id) DO UPDATE SET
    sku               = EXCLUDED.sku,
    product_name      = EXCLUDED.product_name,
    category          = EXCLUDED.category,
    brand             = EXCLUDED.brand,
    list_price        = EXCLUDED.list_price,
    is_active         = EXCLUDED.is_active,
    attributes_json   = EXCLUDED.attributes_json,
    updated_at        = CURRENT_TIMESTAMP,
    etl_batch_id      = EXCLUDED.etl_batch_id,
    source_system     = EXCLUDED.source_system,
    source_record_id  = EXCLUDED.source_record_id
WHERE
    product.sku           IS DISTINCT FROM EXCLUDED.sku
    OR product.product_name IS DISTINCT FROM EXCLUDED.product_name
    OR product.category   IS DISTINCT FROM EXCLUDED.category
    OR product.brand      IS DISTINCT FROM EXCLUDED.brand
    OR product.list_price IS DISTINCT FROM EXCLUDED.list_price
    OR product.is_active  IS DISTINCT FROM EXCLUDED.is_active
    OR product.attributes_json IS DISTINCT FROM EXCLUDED.attributes_json;

-- ---------------------------------------------------
-- sales_order
-- ---------------------------------------------------
INSERT INTO sales_order (
    order_id, customer_id, order_date, order_status, currency, order_total,
    created_at, updated_at, etl_batch_id, source_system, source_record_id
)
SELECT
    order_id, customer_id, order_date, order_status, currency, order_total,
    created_at, updated_at, etl_batch_id, source_system, source_record_id
FROM stg_sales_order
ON CONFLICT (order_id) DO UPDATE SET
    customer_id       = EXCLUDED.customer_id,
    order_date        = EXCLUDED.order_date,
    order_status      = EXCLUDED.order_status,
    currency          = EXCLUDED.currency,
    order_total       = EXCLUDED.order_total,
    updated_at        = CURRENT_TIMESTAMP,
    etl_batch_id      = EXCLUDED.etl_batch_id,
    source_system     = EXCLUDED.source_system,
    source_record_id  = EXCLUDED.source_record_id
WHERE
    sales_order.customer_id  IS DISTINCT FROM EXCLUDED.customer_id
    OR sales_order.order_date   IS DISTINCT FROM EXCLUDED.order_date
    OR sales_order.order_status IS DISTINCT FROM EXCLUDED.order_status
    OR sales_order.currency     IS DISTINCT FROM EXCLUDED.currency
    OR sales_order.order_total  IS DISTINCT FROM EXCLUDED.order_total;

-- ---------------------------------------------------
-- order_line
-- (no created_at/updated_at/etl_batch_id columns on this table per
-- the Gold schema, so the update list is just the line attributes)
-- ---------------------------------------------------
INSERT INTO order_line (
    order_line_id, order_id, product_id, line_number, quantity, unit_price
)
SELECT
    order_line_id, order_id, product_id, line_number, quantity, unit_price
FROM stg_order_line
ON CONFLICT (order_line_id) DO UPDATE SET
    order_id    = EXCLUDED.order_id,
    product_id  = EXCLUDED.product_id,
    line_number = EXCLUDED.line_number,
    quantity    = EXCLUDED.quantity,
    unit_price  = EXCLUDED.unit_price
WHERE
    order_line.order_id    IS DISTINCT FROM EXCLUDED.order_id
    OR order_line.product_id  IS DISTINCT FROM EXCLUDED.product_id
    OR order_line.line_number IS DISTINCT FROM EXCLUDED.line_number
    OR order_line.quantity    IS DISTINCT FROM EXCLUDED.quantity
    OR order_line.unit_price  IS DISTINCT FROM EXCLUDED.unit_price;

COMMIT;
