# Project Guide

This folder contains the working docs for the student ETL project. The main documentation lives in the wiki; this folder keeps the team-facing structure and weekly progress notes in one place.

## Canonical Docs
- Full onboarding and navigation: [Home](Home.md)
- Pipeline and phase tracking: [Project Flow](project_flow.md)

## Working Structure

```text
CAI4_AIS5_S11_P2/
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
|-- docs/                 <- Optional supporting notes/assets (not canonical)
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
6. Update `wiki/project_flow.md` after each milestone (this is the canonical flow guide).

## Team Roles

The current role ownership and weekly checklist live in [Team Roles](Team-Roles.md).

## Expected Output

Clean customer data ready for analysis, plus a documented project flow that the team can maintain.

