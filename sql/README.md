# SQL Artifacts

This directory is reserved for SQL scripts and database-related artifacts.

## Contents (To Be Added)

- `schema_etl.sql` - Table definitions for staging and dimension tables
- `stored_procedures/` - SQL Server stored procedures for ETL operations
- `views/` - Database views for data warehouse queries
- `migrations/` - Version-controlled schema migrations

## Usage

When implementing Phase 4 (Load to Data Warehouse), add your SQL scripts here for:
1. Creating dimension tables (customers, dates, products)
2. Creating fact tables (transactions, interactions)
3. Stored procedures for incremental loads
4. ETL validation views

All SQL should follow standard naming conventions and include comments.
