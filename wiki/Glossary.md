# Glossary

This page defines every technical term used in this project in plain English. If you are new to data engineering, start here.

---

## ETL Terms

### ETL
**Extract, Transform, Load** -- the three-stage process at the heart of this project.
- **Extract**: Read data from source CSV files in `data/raw/`
- **Transform**: Clean, standardize, and validate the data
- **Load**: Write the clean data to PostgreSQL

### ELT
A variant of ETL where data is loaded first, then transformed inside the database. This project uses the traditional ETL pattern where transformation happens before loading.

### Data Pipeline
A sequence of automated steps that moves data from one place to another, applying transformations along the way. In this project, the pipeline is the `etl/` Python module.

### Orchestration
The process of managing and scheduling when pipeline steps run and in what order. In this project, `etl/main.py` orchestrates the five stages.

### Medallion Architecture
A data organisation pattern with three layers:
- **Bronze**: Raw, unprocessed data (`data/raw/`)
- **Silver**: Cleaned and transformed data (Python ETL output)
- **Gold**: Ready-for-analytics data (`data/clean/` and PostgreSQL tables)

### Data Lineage
The record of where each piece of data came from and what transformations it went through. Tracked here via the `source_system` column and the `etl_batch` audit table.

### Idempotent
A process is idempotent if running it multiple times produces the same result as running it once. The pipeline's upsert logic ensures re-running does not create duplicate records.

---

## Pipeline Terms

### Pipeline
The top-level container for the ETL workflow. Run with `python -m etl` from the project root.

### Stage
A single step inside the pipeline:
- **Extract**: Reads CSV files
- **Transform**: Cleans and normalises data
- **Validate**: Checks data quality
- **Load**: Upserts into PostgreSQL
- **Reconcile**: Verifies row counts

### Staging Table
A temporary table used as a buffer during data loading. The pipeline loads transformed data into `stg_*` tables first, then upserts into gold tables, then truncates staging.

### Upsert
A database operation that inserts a row if it does not exist or updates it if it does -- based on a matching key. Used in `04_load_procedures.sql` to load data without duplicating rows.

### View
A saved SQL query that you can query like a table. Views do not store data -- they re-run their underlying query each time.

### Stored Procedure
A saved, named SQL script that you can call by name. In this project, procedures in `04_load_procedures.sql` handle the staging → gold upsert logic.

### TRUNCATE
A SQL command that deletes all rows from a table quickly. Used to clear staging tables before each load.

---

## Data Quality Terms

### Deduplication
Removing duplicate records. In this project, if two contacts have the same `email`, only one is kept (the one with the fewest null fields).

### Null
A missing or unknown value in a database. Different from an empty string or zero. This project rejects rows where a primary key is NULL.

### Data Type Casting
Converting a value from one data type to another. For example, converting the string `"2023-05-10"` to a proper SQL `DATE` value, or converting `"1001"` (string) to `1001` (integer).

### Validation Query
A SQL query written specifically to check whether data meets quality standards (e.g. no nulls, no duplicates, values in expected ranges). This project's validation queries are in `scripts/sql/scripts/05_validation_queries.sql`.

### Rejected Record
A row that fails a validation check and is excluded from the clean output. Written to `data/rejected/` for investigation.

### Quarantined Record
A row with recoverable issues (e.g. duplicate email, FK orphan) that is written to `data/quarantine/` for review.

---

## PostgreSQL Terms

### PostgreSQL
The open-source relational database used as the pipeline target. The project database is `crm_db`.

### Schema
A namespace for database objects. This project uses the default `public` schema for gold tables (e.g. `public.contact`, `public.customer`).

### Primary Key
A column (or set of columns) whose value uniquely identifies each row in a table. Cannot be NULL or duplicate.

### Foreign Key (FK)
A column that references a primary key in another table, ensuring referential integrity.

### COPY
A PostgreSQL command for bulk loading data from CSV files. Used by the load stage to efficiently populate staging tables.

---

## Git / GitHub Terms

### Branch
An independent line of development in Git. You create a branch to work on a feature or fix without affecting `main`. When the work is done, you merge the branch back.

### Pull Request (PR)
A request to merge your branch into `main`. Pull requests are reviewed by teammates before merging to catch bugs and ensure quality.

### Commit
A saved snapshot of your changes in Git. Each commit has a message describing what changed.

### Merge
Combining changes from one branch into another.

### Clone
Downloading a copy of the repository to your local machine: `git clone <url>`.

### Push
Uploading your local commits to GitHub so others can see them and you can open a pull request.

### Issue
A GitHub feature for tracking tasks, bugs, and feature requests.
