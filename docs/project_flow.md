# Project Phases Guide

## ETL for Customer Data from Multiple Sources

This guide breaks the project into 5 simple phases, aligned with the 5 team roles.

---

## Phase 1 — Data Collection / Extraction
**Owner:** Team Member 1

### Tasks
- Collect CRM export data.
- Collect Excel customer/sales files.
- Check basic format (headers, encoding, date format).
- Save all original files in `data/raw/`.

### Deliverable
- Raw source files organized inside `data/raw/`.

---

## Phase 2 — Data Cleaning / Transformation (ETL)
**Owner:** Team Member 2

### Tasks
- Build ETL steps in Azure Data Factory.
- Create/update:
	- `adf/linked_services/`
	- `adf/datasets/`
	- `adf/pipelines/`
- Apply transformations:
	- remove duplicates
	- handle nulls
	- standardize names and data types

### Deliverable
- ADF assets saved in `adf/` folders.
- Clean transformed output in `data/clean/`.

---

## Phase 3 — Data Modeling / Warehouse Design
**Owner:** Team Member 3

### Tasks
- Define target warehouse table design.
- Create SQL scripts for table creation and load logic.
- Save scripts in `sql/scripts/`.

### Deliverable
- SQL scripts ready to build target model in SQL Server.

---

## Phase 4 — Data Validation / Testing
**Owner:** Team Member 4

### Tasks
- Validate row counts before/after ETL.
- Verify no critical nulls in required fields.
- Verify no unexpected duplicates.
- Check sample records for correctness.

### Deliverable
- Validation checklist completed (can be added in this file as notes).

---

## Phase 5 — Documentation & Presentation
**Owner:** Team Member 5

### Tasks
- Maintain `docs/README.md` and this phase guide.
- Document final pipeline flow (source → transform → output).
- Prepare final presentation (screenshots + summary results).

### Deliverable
- Final project documentation and presentation deck.

---

## Suggested Timeline (Simple)
- Week 1: Phase 1 + start Phase 2
- Week 2: Finish Phase 2 + Phase 3
- Week 3: Phase 4
- Week 4: Phase 5 and final presentation

---

## Progress Tracker

| Phase | Owner | Status | Notes |
|---|---|---|---|
| 1. Collection / Extraction | Member 1 | Pending | |
| 2. Cleaning / Transformation | Member 2 | Pending | |
| 3. Modeling / Warehouse | Member 3 | Pending | |
| 4. Validation / Testing | Member 4 | Pending | |
| 5. Documentation / Presentation | Member 5 | Pending | |

