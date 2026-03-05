# Project Workflow Guide (DEPI Final Project - Iterative)

## ETL for Customer Data from Multiple Sources

This project follows a practical iterative workflow for a 4-week DEPI final project.
The team works in overlapping cycles so each cycle improves the pipeline quality and output.

---

## Team Roles and Assignments (Working in Parallel)

- **Ali — Data Collection / Extraction**
	- Collect CRM and Excel source files.
	- Maintain incoming files in `data/raw/`.

- **Josephine — Data Cleaning / Transformation (ETL)**
	- Build and improve ADF flow assets in:
		- `adf/linked_services/`
		- `adf/datasets/`
		- `adf/pipelines/`
	- Apply cleaning and transformation rules.

- **Mohamed — Data Modeling / Warehouse Design**
	- Draft and refine SQL Server schema and load scripts in `sql/scripts/`.
	- Work at the same time as extraction and ETL to avoid blockers.

- **Sara — Data Validation / Testing**
	- Continuously validate row counts, nulls, duplicates, and data consistency.
	- Test every cycle, not only at project end.

- **Mohab — Documentation & Presentation**
	- Keep `docs/README.md` and `docs/project_flow.md` updated.
	- Prepare final report and presentation artifacts.

---

## Iterative Delivery Cycles (4 Weeks)

## Cycle 1 (Week 1): Minimal Viable Pipeline

### Goal
Deliver the first working version using sample CRM + Excel data.

### Parallel Work
- Ali places sample source files in `data/raw/`.
- Josephine builds first ADF pipeline path raw → clean.
- Mohamed drafts initial table scripts in `sql/scripts/`.
- Sara validates basic output quality.
- Mohab documents setup and first results in `docs/`.

### Expected Output
- First successful run producing cleaned output in `data/clean/`.

---

## Cycle 2 (Week 2-3): Full Data Load + Automated Transformations

### Goal
Scale from sample data to full data and strengthen transformation rules.

### Parallel Work
- Ali updates `data/raw/` with fuller and newer files.
- Josephine adds robust transformations (null handling, deduplication, standardization).
- Mohamed updates SQL scripts for improved warehouse design.
- Sara runs repeated checks after each update and logs issues.
- Mohab keeps documentation current and records decisions.

### Expected Output
- Stable pipeline with automated transformations and cleaner, consistent outputs.

---

## Cycle 3 (Week 4): Data Validation + Final Presentation

### Goal
Finalize quality, freeze outputs, and prepare final DEPI presentation.

### Parallel Work
- Ali performs final source refresh in `data/raw/`.
- Josephine finalizes ADF pipeline behavior and run order.
- Mohamed finalizes SQL scripts in `sql/scripts/`.
- Sara executes final validation checklist and confirms readiness.
- Mohab prepares final report/storyline and presentation materials.

### Expected Output
- Final clean data in `data/clean/`.
- Final ADF assets and SQL scripts.
- Portfolio-ready final project documentation.

---

## Folder Usage Reference

- `data/raw/` → source CRM and Excel files
- `data/clean/` → transformed output ready for analytics
- `adf/pipelines/` → orchestration pipelines
- `adf/datasets/` → source/target datasets
- `adf/linked_services/` → service connections
- `sql/scripts/` → schema + transformation/load scripts
- `docs/README.md` + `docs/project_flow.md` → documentation, status, and final narrative

---

## Iterative Progress Tracker

Update this table at least once per week:

| Cycle | Focus | Ali (Extraction) | Josephine (ETL) | Mohamed (Modeling) | Sara (Testing) | Mohab (Docs) | Cycle Status |
|---|---|---|---|---|---|---|---|
| Cycle 1 | MVP pipeline with sample data | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Planned / Active / Complete |
| Cycle 2 | Full load + automated transformations | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Planned / Active / Complete |
| Cycle 3 | Final validation + presentation | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Not Started / In Progress / Done | Planned / Active / Complete |


