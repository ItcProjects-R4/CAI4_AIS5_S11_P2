# Project Guide

This folder contains the working docs for the student ETL project. The main documentation lives in the wiki; this folder keeps the team-facing structure and weekly progress notes in one place.

## Canonical Docs
- Full onboarding and navigation: [../wiki/Home.md](../wiki/Home.md)
- Pipeline and phase tracking: [project_flow.md](project_flow.md)

## Working Structure

```text
customer-data-etl/
|-- data/
|   |-- raw/
|   |-- clean/
|   |-- rejected/
|   `-- quarantine/
|-- sql/
|   `-- scripts/
|-- adf/
|   |-- pipelines/
|   |-- datasets/
|   `-- linked_services/
|-- docs/
|   |-- README.md
|   `-- project_flow.md
|-- wiki/
|-- presentation/
`-- .github/
    |-- ISSUE_TEMPLATE/
    |-- PULL_REQUEST_TEMPLATE.md
    `-- workflows/
```

## Quick Rules
1. Put source input files in `data/raw/`.
2. Keep rejected records in `data/rejected/` and temporary problem files in `data/quarantine/`.
3. Keep transformed output in `data/clean/`.
4. Save every SQL change as a new numbered script in `sql/scripts/`.
5. Export ADF JSON assets into `adf/` folders.
6. Update `docs/project_flow.md` after each milestone.

## Team Roles

The current role ownership and weekly checklist live in [../wiki/Team-Roles.md](../wiki/Team-Roles.md).

## Expected Output

Clean customer data ready for analysis, plus a documented project flow that the team can maintain.

