-- Staging tables: no FK, PK, UNIQUE, or CHECK constraints
CREATE TABLE IF NOT EXISTS stg_etl_batch (
    etl_batch_id VARCHAR(36) NULL,
    pipeline_run_id VARCHAR(255) NULL,
    started_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,
    status VARCHAR(50) NULL,
    notes TEXT NULL
);

CREATE TABLE IF NOT EXISTS stg_contact (
    contact_id VARCHAR(36) NULL,
    email VARCHAR(320) NULL,
    full_name VARCHAR(255) NULL,
    phone VARCHAR(50) NULL,
    country VARCHAR(100) NULL,
    address_line1 VARCHAR(500) NULL,
    city VARCHAR(100) NULL,
    state VARCHAR(100) NULL,
    postal_code VARCHAR(20) NULL,
    company_name VARCHAR(255) NULL,
    department VARCHAR(255) NULL,
    job_title VARCHAR(255) NULL,
    attributes_json TEXT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    etl_batch_id VARCHAR(36) NULL,
    source_system VARCHAR(100) NULL,
    source_record_id VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS stg_customer (
    customer_id VARCHAR(36) NULL,
    contact_id VARCHAR(36) NULL,
    customer_since DATE NULL,
    status VARCHAR(50) NULL,
    segment VARCHAR(100) NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    etl_batch_id VARCHAR(36) NULL,
    source_system VARCHAR(100) NULL,
    source_record_id VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS stg_product (
    product_id VARCHAR(36) NULL,
    sku VARCHAR(100) NULL,
    product_name VARCHAR(500) NULL,
    category VARCHAR(255) NULL,
    brand VARCHAR(255) NULL,
    list_price DECIMAL(18, 4) NULL,
    is_active BOOLEAN NULL,
    attributes_json TEXT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    etl_batch_id VARCHAR(36) NULL,
    source_system VARCHAR(100) NULL,
    source_record_id VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS stg_sales_order (
    order_id VARCHAR(36) NULL,
    customer_id VARCHAR(36) NULL,
    order_date TIMESTAMP NULL,
    order_status VARCHAR(50) NULL,
    currency CHAR(3) NULL,
    order_total DECIMAL(18, 4) NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    etl_batch_id VARCHAR(36) NULL,
    source_system VARCHAR(100) NULL,
    source_record_id VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS stg_order_line (
    order_line_id VARCHAR(36) NULL,
    order_id VARCHAR(36) NULL,
    product_id VARCHAR(36) NULL,
    line_number INTEGER NULL,
    quantity INTEGER NULL,
    unit_price DECIMAL(18, 4) NULL
);