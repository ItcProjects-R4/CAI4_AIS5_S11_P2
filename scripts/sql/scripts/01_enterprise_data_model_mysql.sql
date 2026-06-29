-- =====================================================================
-- shopOrder schema (PostgreSQL version)
-- =====================================================================
-- Note: PostgreSQL cannot DROP/CREATE a database while connected to it
-- and does not support "USE <db>". Run the DROP/CREATE DATABASE block
-- from a different database (e.g. psql -d postgres), then connect to
-- shopOrder and run the rest of the script.
-- ---------------------------------------------------------------------

-- Run this part while connected to e.g. "postgres":
DROP DATABASE IF EXISTS shopOrder;
CREATE DATABASE shopOrder
    ENCODING 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE   = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Now connect to the new database before running the rest:
-- \c shopOrder

-- ---------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS etl_batch (
    etl_batch_id    VARCHAR(36)   NOT NULL,
    pipeline_run_id VARCHAR(255)  NULL,
    started_at      TIMESTAMP     NULL,
    ended_at        TIMESTAMP     NULL,
    status          VARCHAR(50)   NULL,
    notes           TEXT          NULL,

    CONSTRAINT pk_etl_batch PRIMARY KEY (etl_batch_id)
);

CREATE TABLE IF NOT EXISTS contact (
    contact_id        VARCHAR(36)   NOT NULL,
    email             VARCHAR(320)  NOT NULL,
    full_name         VARCHAR(255)  NULL,
    phone             VARCHAR(50)   NULL,
    country           VARCHAR(100)  NULL,

    address_line1     VARCHAR(500)  NULL,
    city              VARCHAR(100)  NULL,
    state             VARCHAR(100)  NULL,
    postal_code       VARCHAR(20)   NULL,

    company_name      VARCHAR(255)  NULL,
    department        VARCHAR(255)  NULL,
    job_title         VARCHAR(255)  NULL,

    attributes_json   TEXT          NULL,
    created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP     NULL,

    etl_batch_id      VARCHAR(36)   NOT NULL,
    source_system     VARCHAR(100)  NULL,
    source_record_id  VARCHAR(255)  NULL,

    CONSTRAINT pk_contact           PRIMARY KEY (contact_id),
    CONSTRAINT uq_contact_email     UNIQUE (email),

    CONSTRAINT fk_contact_etl_batch
        FOREIGN KEY (etl_batch_id)
        REFERENCES etl_batch (etl_batch_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_contact_etl_batch_id ON contact (etl_batch_id);
CREATE INDEX idx_contact_email        ON contact (email);
CREATE INDEX idx_contact_country      ON contact (country);

CREATE TABLE IF NOT EXISTS customer (
    customer_id      VARCHAR(36)   NOT NULL,
    contact_id       VARCHAR(36)   NOT NULL,

    customer_since   DATE          NULL,
    status           VARCHAR(50)   NULL,
    segment          VARCHAR(100)  NULL,

    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP     NULL,

    etl_batch_id     VARCHAR(36)   NOT NULL,
    source_system    VARCHAR(100)  NULL,
    source_record_id VARCHAR(255)  NULL,

    CONSTRAINT pk_customer          PRIMARY KEY (customer_id),
    CONSTRAINT uq_customer_contact  UNIQUE (contact_id),

    CONSTRAINT fk_customer_contact
        FOREIGN KEY (contact_id)
        REFERENCES contact (contact_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_customer_etl_batch
        FOREIGN KEY (etl_batch_id)
        REFERENCES etl_batch (etl_batch_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_customer_contact_id   ON customer (contact_id);
CREATE INDEX idx_customer_etl_batch_id ON customer (etl_batch_id);
CREATE INDEX idx_customer_status       ON customer (status);
CREATE INDEX idx_customer_segment      ON customer (segment);

CREATE TABLE IF NOT EXISTS product (
    product_id       VARCHAR(36)    NOT NULL,
    sku              VARCHAR(100)   NOT NULL,
    product_name     VARCHAR(500)   NOT NULL,
    category         VARCHAR(255)   NULL,
    brand            VARCHAR(255)   NULL,
    list_price       DECIMAL(18,4)  NULL,
    is_active        BOOLEAN        NOT NULL DEFAULT TRUE,

    attributes_json  TEXT           NULL,
    created_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP      NULL,

    etl_batch_id     VARCHAR(36)    NOT NULL,
    source_system    VARCHAR(100)   NULL,
    source_record_id VARCHAR(255)   NULL,

    CONSTRAINT pk_product            PRIMARY KEY (product_id),
    CONSTRAINT uq_product_sku        UNIQUE (sku),
    CONSTRAINT ck_product_list_price CHECK (list_price >= 0),

    CONSTRAINT fk_product_etl_batch
        FOREIGN KEY (etl_batch_id)
        REFERENCES etl_batch (etl_batch_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_product_etl_batch_id ON product (etl_batch_id);
CREATE INDEX idx_product_sku          ON product (sku);
CREATE INDEX idx_product_category     ON product (category);
CREATE INDEX idx_product_brand        ON product (brand);
CREATE INDEX idx_product_is_active    ON product (is_active);

CREATE TABLE IF NOT EXISTS sales_order (
    order_id         VARCHAR(36)    NOT NULL,
    customer_id      VARCHAR(36)    NOT NULL,

    order_date       TIMESTAMP      NOT NULL,
    order_status     VARCHAR(50)    NULL,
    currency         CHAR(3)        NULL,
    order_total      DECIMAL(18,4)  NULL,

    created_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP      NULL,

    etl_batch_id     VARCHAR(36)    NOT NULL,
    source_system    VARCHAR(100)   NULL,
    source_record_id VARCHAR(255)   NULL,

    CONSTRAINT pk_sales_order        PRIMARY KEY (order_id),
    CONSTRAINT ck_sales_order_total  CHECK (order_total >= 0),

    CONSTRAINT fk_sales_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer (customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_sales_order_etl_batch
        FOREIGN KEY (etl_batch_id)
        REFERENCES etl_batch (etl_batch_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_sales_order_customer_id  ON sales_order (customer_id);
CREATE INDEX idx_sales_order_etl_batch_id ON sales_order (etl_batch_id);
CREATE INDEX idx_sales_order_order_date   ON sales_order (order_date);
CREATE INDEX idx_sales_order_order_status ON sales_order (order_status);
CREATE INDEX idx_sales_order_currency     ON sales_order (currency);

CREATE TABLE IF NOT EXISTS order_line (
    order_line_id    VARCHAR(36)    NOT NULL,
    order_id         VARCHAR(36)    NOT NULL,
    product_id       VARCHAR(36)    NOT NULL,

    line_number      INT            NOT NULL,
    quantity         INT            NOT NULL,
    unit_price       DECIMAL(18,4)  NOT NULL,

    CONSTRAINT pk_order_line             PRIMARY KEY (order_line_id),
    CONSTRAINT uq_order_line_number      UNIQUE (order_id, line_number),
    CONSTRAINT ck_order_line_quantity    CHECK (quantity > 0),
    CONSTRAINT ck_order_line_unit_price  CHECK (unit_price >= 0),

    CONSTRAINT fk_order_line_order
        FOREIGN KEY (order_id)
        REFERENCES sales_order (order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_order_line_product
        FOREIGN KEY (product_id)
        REFERENCES product (product_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_order_line_order_id   ON order_line (order_id);
CREATE INDEX idx_order_line_product_id ON order_line (product_id);
