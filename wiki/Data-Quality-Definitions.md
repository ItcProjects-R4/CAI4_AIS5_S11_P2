# Data Quality Definitions

## Rejected

**Rejected** records are rows that are fundamentally unrecoverable and permanently excluded from the pipeline output. A record is rejected when it is missing one or more critical business identity fields — such as a primary key (`contact_id`, `order_id`), a mandatory business field (`email` for contacts, `order_date` for orders), or when a required value is so corrupt that no reasonable transformation can salvage it (e.g., a completely unparseable date string like `"19967--30"`). Rejected records are written to `data/rejected/<entity>.csv` and are never loaded into the Gold layer (database). They represent data that the source system should fix before re-extraction.

## Quarantine

**Quarantined** records are rows that have a valid identity (their primary key exists and is non-null) but exhibit data quality issues that make them unsuitable for immediate loading into the production database. Common reasons for quarantine include: medium or high severity DQ flags from the source (e.g., swapped field values, garbled encoding), violation of a foreign key constraint due to a parent record being absent from the clean set (FK cascade quarantine — e.g., a customer whose contact was deduplicated away), or duplicate records that were not the winning survivor during deduplication. Quarantined records are written to `data/quarantine/<entity>.csv` and are available for manual review, correction, and potential re-ingestion in a future pipeline run. They are explicitly excluded from the Gold layer load.

## Clean

**Clean** records have passed all validation checks: NOT NULL constraints on required fields, foreign key referential integrity (every FK points to a row that exists in the clean split of its parent table), UNIQUE key constraints (no duplicate emails, SKUs, or order lines), and CHECK constraints (non-negative prices, positive quantities). Clean records are written to `data/clean/<entity>.csv` and are the only records loaded into the MySQL `shopOrder` database during the Gold/Load phase.

## Summary Table

| Tier | Output Path | Loadable? | Action Required |
|---|---|---|---|
| **Clean** | `data/clean/<entity>.csv` | Yes — ready for Gold/SQL load | None |
| **Quarantine** | `data/quarantine/<entity>.csv` | No — held for review | Manual review; may be correctable |
| **Rejected** | `data/rejected/<entity>.csv` | No — permanently excluded | Fix at source system level |
