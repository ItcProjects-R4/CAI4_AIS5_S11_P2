-- 03_create_views.sql
-- PostgreSQL views built on the Gold layer tables in crm_db
-- Read-only: no tables created, no data modified.

-- =========================================================
-- vw_customer_summary
-- Customer identity + linked contact details
-- =========================================================
CREATE OR REPLACE VIEW public.vw_customer_summary AS
SELECT
    c.customer_id,
    c.contact_id,
    c.customer_since,
    c.status,
    c.segment,
    ct.full_name,
    ct.email,
    ct.phone,
    ct.country,
    ct.state,
    ct.city,
    ct.address_line1,
    ct.postal_code,
    ct.company_name,
    ct.department,
    ct.job_title,
    c.source_system
FROM public.customer c
JOIN public.contact ct
    ON ct.contact_id = c.contact_id;

-- =========================================================
-- vw_sales_summary
-- Order + line level detail with customer and product context
-- =========================================================
CREATE OR REPLACE VIEW public.vw_sales_summary AS
SELECT
    so.order_id,
    so.order_date,
    so.order_status,
    so.currency,
    so.order_total,
    so.customer_id,
    ct.full_name        AS customer_name,
    ol.order_line_id,
    ol.line_number,
    p.product_id,
    p.product_name,
    p.category,
    ol.quantity,
    ol.unit_price,
    (ol.quantity * ol.unit_price) AS line_total,
    so.created_at,
    so.updated_at
FROM public.sales_order so
JOIN public.customer c
    ON c.customer_id = so.customer_id
JOIN public.contact ct
    ON ct.contact_id = c.contact_id
JOIN public.order_line ol
    ON ol.order_id = so.order_id
JOIN public.product p
    ON p.product_id = ol.product_id;

-- =========================================================
-- vw_governorate_revenue
-- Revenue, customer count, and order count by governorate (contact.state)
-- =========================================================
CREATE OR REPLACE VIEW public.vw_governorate_revenue AS
SELECT
    ct.state AS governorate,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(DISTINCT so.order_id)   AS order_count,
    COALESCE(SUM(ol.quantity * ol.unit_price), 0) AS revenue
FROM public.contact ct
JOIN public.customer c
    ON c.contact_id = ct.contact_id
LEFT JOIN public.sales_order so
    ON so.customer_id = c.customer_id
LEFT JOIN public.order_line ol
    ON ol.order_id = so.order_id
GROUP BY ct.state;

-- =========================================================
-- vw_top_products
-- Units sold, revenue, and order count by product
-- =========================================================
CREATE OR REPLACE VIEW public.vw_top_products AS
SELECT
    p.product_name,
    p.category,
    SUM(ol.quantity)                       AS units_sold,
    SUM(ol.quantity * ol.unit_price)       AS revenue,
    COUNT(DISTINCT ol.order_id)            AS order_count
FROM public.product p
JOIN public.order_line ol
    ON ol.product_id = p.product_id
GROUP BY p.product_name, p.category;
