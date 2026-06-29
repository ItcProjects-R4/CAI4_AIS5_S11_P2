-- 02_create_tables.sql
-- PostgreSQL, combined Gold + Staging tables for crm_db

CREATE SCHEMA IF NOT EXISTS public;

-- =========================================================
-- Gold layer
-- =========================================================

-- Table: public.etl_batch
CREATE TABLE IF NOT EXISTS public.etl_batch
(
    etl_batch_id    VARCHAR(36)  NOT NULL,
    pipeline_run_id VARCHAR(255),
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    status          VARCHAR(50),
    notes           TEXT,
    CONSTRAINT pk_etl_batch PRIMARY KEY (etl_batch_id)
);

ALTER TABLE IF EXISTS public.etl_batch
    OWNER TO postgres;

-- Table: public.contact
CREATE TABLE IF NOT EXISTS public.contact
(
    contact_id       VARCHAR(36)  NOT NULL,
    email            VARCHAR(320) NOT NULL,
    full_name        VARCHAR(255),
    phone            VARCHAR(50),
    country          VARCHAR(100),
    address_line1    VARCHAR(500),
    city             VARCHAR(100),
    state            VARCHAR(100),
    postal_code      VARCHAR(20),
    company_name     VARCHAR(255),
    department       VARCHAR(255),
    job_title        VARCHAR(255),
    attributes_json  TEXT,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)  NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    CONSTRAINT pk_contact PRIMARY KEY (contact_id),
    CONSTRAINT uq_contact_email UNIQUE (email),
    CONSTRAINT fk_contact_etl_batch FOREIGN KEY (etl_batch_id)
        REFERENCES public.etl_batch (etl_batch_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

ALTER TABLE IF EXISTS public.contact
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_contact_country
    ON public.contact (country);

CREATE INDEX IF NOT EXISTS idx_contact_email
    ON public.contact (email);

CREATE INDEX IF NOT EXISTS idx_contact_etl_batch_id
    ON public.contact (etl_batch_id);

-- Table: public.customer
CREATE TABLE IF NOT EXISTS public.customer
(
    customer_id      VARCHAR(36)  NOT NULL,
    contact_id       VARCHAR(36)  NOT NULL,
    customer_since   DATE,
    status           VARCHAR(50),
    segment          VARCHAR(100),
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)  NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    CONSTRAINT pk_customer PRIMARY KEY (customer_id),
    CONSTRAINT uq_customer_contact UNIQUE (contact_id),
    CONSTRAINT fk_customer_contact FOREIGN KEY (contact_id)
        REFERENCES public.contact (contact_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_customer_etl_batch FOREIGN KEY (etl_batch_id)
        REFERENCES public.etl_batch (etl_batch_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

ALTER TABLE IF EXISTS public.customer
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_customer_contact_id
    ON public.customer (contact_id);

CREATE INDEX IF NOT EXISTS idx_customer_etl_batch_id
    ON public.customer (etl_batch_id);

CREATE INDEX IF NOT EXISTS idx_customer_segment
    ON public.customer (segment);

CREATE INDEX IF NOT EXISTS idx_customer_status
    ON public.customer (status);

-- Table: public.product
CREATE TABLE IF NOT EXISTS public.product
(
    product_id       VARCHAR(36)   NOT NULL,
    sku              VARCHAR(100)  NOT NULL,
    product_name     VARCHAR(500)  NOT NULL,
    category         VARCHAR(255),
    brand            VARCHAR(255),
    list_price       NUMERIC(18,4),
    is_active        BOOLEAN       NOT NULL DEFAULT TRUE,
    attributes_json  TEXT,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)   NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    CONSTRAINT pk_product PRIMARY KEY (product_id),
    CONSTRAINT uq_product_sku UNIQUE (sku),
    CONSTRAINT fk_product_etl_batch FOREIGN KEY (etl_batch_id)
        REFERENCES public.etl_batch (etl_batch_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT ck_product_list_price CHECK (list_price IS NULL OR list_price >= 0)
);

ALTER TABLE IF EXISTS public.product
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_product_brand
    ON public.product (brand);

CREATE INDEX IF NOT EXISTS idx_product_category
    ON public.product (category);

CREATE INDEX IF NOT EXISTS idx_product_etl_batch_id
    ON public.product (etl_batch_id);

CREATE INDEX IF NOT EXISTS idx_product_is_active
    ON public.product (is_active);

CREATE INDEX IF NOT EXISTS idx_product_sku
    ON public.product (sku);

-- Table: public.sales_order
CREATE TABLE IF NOT EXISTS public.sales_order
(
    order_id         VARCHAR(36)   NOT NULL,
    customer_id      VARCHAR(36)   NOT NULL,
    order_date       TIMESTAMP     NOT NULL,
    order_status     VARCHAR(50),
    currency         CHAR(3),
    order_total      NUMERIC(18,4),
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)   NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    CONSTRAINT pk_sales_order PRIMARY KEY (order_id),
    CONSTRAINT fk_sales_order_customer FOREIGN KEY (customer_id)
        REFERENCES public.customer (customer_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_sales_order_etl_batch FOREIGN KEY (etl_batch_id)
        REFERENCES public.etl_batch (etl_batch_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT ck_sales_order_total CHECK (order_total IS NULL OR order_total >= 0)
);

ALTER TABLE IF EXISTS public.sales_order
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_sales_order_currency
    ON public.sales_order (currency);

CREATE INDEX IF NOT EXISTS idx_sales_order_customer_id
    ON public.sales_order (customer_id);

CREATE INDEX IF NOT EXISTS idx_sales_order_etl_batch_id
    ON public.sales_order (etl_batch_id);

CREATE INDEX IF NOT EXISTS idx_sales_order_order_date
    ON public.sales_order (order_date);

CREATE INDEX IF NOT EXISTS idx_sales_order_order_status
    ON public.sales_order (order_status);

-- Table: public.order_line
CREATE TABLE IF NOT EXISTS public.order_line
(
    order_line_id    VARCHAR(36)   NOT NULL,
    order_id         VARCHAR(36)   NOT NULL,
    product_id       VARCHAR(36)   NOT NULL,
    line_number      INTEGER       NOT NULL,
    quantity         INTEGER       NOT NULL,
    unit_price       NUMERIC(18,4) NOT NULL,
    CONSTRAINT pk_order_line PRIMARY KEY (order_line_id),
    CONSTRAINT uq_order_line_number UNIQUE (order_id, line_number),
    CONSTRAINT fk_order_line_order FOREIGN KEY (order_id)
        REFERENCES public.sales_order (order_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_order_line_product FOREIGN KEY (product_id)
        REFERENCES public.product (product_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT ck_order_line_quantity CHECK (quantity > 0),
    CONSTRAINT ck_order_line_unit_price CHECK (unit_price >= 0)
);

ALTER TABLE IF EXISTS public.order_line
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_order_line_order_id
    ON public.order_line (order_id);

CREATE INDEX IF NOT EXISTS idx_order_line_product_id
    ON public.order_line (product_id);

-- =========================================================
-- Staging layer
-- =========================================================

-- Table: public.stg_etl_batch
CREATE TABLE IF NOT EXISTS public.stg_etl_batch
(
    etl_batch_id    VARCHAR(36)  NOT NULL,
    pipeline_run_id VARCHAR(255),
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    status          VARCHAR(50),
    notes           TEXT,
    load_timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stg_etl_batch_pkey PRIMARY KEY (etl_batch_id)
);

ALTER TABLE IF EXISTS public.stg_etl_batch
    OWNER TO postgres;

-- Table: public.stg_contact
CREATE TABLE IF NOT EXISTS public.stg_contact
(
    contact_id       VARCHAR(36)  NOT NULL,
    email            VARCHAR(320) NOT NULL,
    full_name        VARCHAR(255),
    phone            VARCHAR(50),
    country          VARCHAR(100),
    address_line1    VARCHAR(500),
    city             VARCHAR(100),
    state            VARCHAR(100),
    postal_code      VARCHAR(20),
    company_name     VARCHAR(255),
    department       VARCHAR(255),
    job_title        VARCHAR(255),
    attributes_json  TEXT,
    created_at       TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)  NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    load_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stg_contact_pkey PRIMARY KEY (contact_id)
);

ALTER TABLE IF EXISTS public.stg_contact
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_stg_contact_email
    ON public.stg_contact (email);

CREATE INDEX IF NOT EXISTS idx_stg_contact_etl_batch_id
    ON public.stg_contact (etl_batch_id);

-- Table: public.stg_customer
CREATE TABLE IF NOT EXISTS public.stg_customer
(
    customer_id      VARCHAR(36)  NOT NULL,
    contact_id       VARCHAR(36),
    customer_since   DATE,
    status           VARCHAR(50),
    segment          VARCHAR(100),
    created_at       TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)  NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    load_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stg_customer_pkey PRIMARY KEY (customer_id)
);

ALTER TABLE IF EXISTS public.stg_customer
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_stg_customer_contact_id
    ON public.stg_customer (contact_id);

CREATE INDEX IF NOT EXISTS idx_stg_customer_etl_batch_id
    ON public.stg_customer (etl_batch_id);

-- Table: public.stg_product
CREATE TABLE IF NOT EXISTS public.stg_product
(
    product_id       VARCHAR(36)   NOT NULL,
    sku              VARCHAR(100)  NOT NULL,
    product_name     VARCHAR(500)  NOT NULL,
    category         VARCHAR(255),
    brand            VARCHAR(255),
    list_price       NUMERIC(18,4),
    is_active        BOOLEAN       NOT NULL,
    attributes_json  TEXT,
    created_at       TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)   NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    load_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stg_product_pkey PRIMARY KEY (product_id)
);

ALTER TABLE IF EXISTS public.stg_product
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_stg_product_sku
    ON public.stg_product (sku);

CREATE INDEX IF NOT EXISTS idx_stg_product_etl_batch_id
    ON public.stg_product (etl_batch_id);

-- Table: public.stg_sales_order
CREATE TABLE IF NOT EXISTS public.stg_sales_order
(
    order_id         VARCHAR(36)   NOT NULL,
    customer_id      VARCHAR(36)   NOT NULL,
    order_date       TIMESTAMP     NOT NULL,
    order_status     VARCHAR(50),
    currency         CHAR(3),
    order_total      NUMERIC(18,4),
    created_at       TIMESTAMP,
    updated_at       TIMESTAMP,
    etl_batch_id     VARCHAR(36)   NOT NULL,
    source_system    VARCHAR(100),
    source_record_id VARCHAR(255),
    load_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stg_sales_order_pkey PRIMARY KEY (order_id)
);

ALTER TABLE IF EXISTS public.stg_sales_order
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_stg_sales_order_customer_id
    ON public.stg_sales_order (customer_id);

CREATE INDEX IF NOT EXISTS idx_stg_sales_order_etl_batch_id
    ON public.stg_sales_order (etl_batch_id);

-- Table: public.stg_order_line
CREATE TABLE IF NOT EXISTS public.stg_order_line
(
    order_line_id    VARCHAR(36)   NOT NULL,
    order_id         VARCHAR(36)   NOT NULL,
    product_id       VARCHAR(36)   NOT NULL,
    line_number      INTEGER       NOT NULL,
    quantity         INTEGER       NOT NULL,
    unit_price       NUMERIC(18,4) NOT NULL,
    load_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stg_order_line_pkey PRIMARY KEY (order_line_id)
);

ALTER TABLE IF EXISTS public.stg_order_line
    OWNER TO postgres;

CREATE INDEX IF NOT EXISTS idx_stg_order_line_order_id
    ON public.stg_order_line (order_id);

CREATE INDEX IF NOT EXISTS idx_stg_order_line_product_id
    ON public.stg_order_line (product_id);
