-- PostgreSQL data loading examples
-- Note: Data is primarily loaded via Python using pandas.to_sql()

-- Example using COPY command (requires server-side file access):
-- COPY stg_customer (customer_id, contact_id, customer_since, status, segment, created_at, updated_at, etl_batch_id, source_system, source_record_id)
-- FROM '/var/lib/postgresql/data/customers.csv'
-- WITH (FORMAT csv, HEADER, DELIMITER ',', QUOTE '"', NULL '');

-- Alternatively use client-side loading through pandas/to_sql as implemented in Python loaders.