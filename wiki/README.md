# Wiki README

This file is the index for all markdown documentation in `wiki/`.

## Core Entry Points

- [Home](./Home.md)
- [Project Flow](./project_flow.md)
- [Contributing](./Contributing.md)

## All Wiki Markdown Files

| File | Purpose |
|---|---|
| [README.md](./README.md) | Wiki index and quick navigation. |
| [Home.md](./Home.md) | Main project overview and wiki navigation. |
| [project_flow.md](./project_flow.md) | Planning flow, role knowledge, deliverables, and timeline. |
| [Contributing.md](./Contributing.md) | Branching, pull requests, ownership, and collaboration workflow. |
| [Project-Architecture.md](./Project-Architecture.md) | Architecture layers and design rationale. |
| [ETL-Pipeline.md](./ETL-Pipeline.md) | End-to-end pipeline behavior and execution notes. |
| [Data-Sources.md](./Data-Sources.md) | Source systems, fields, and ingestion context. |
| [SQL-Schema.md](./SQL-Schema.md) | SQL tables, views, procedures, and script guidance. |
| [Data-Validation.md](./Data-Validation.md) | Data quality checks and validation process. |
| [Setup-Guide.md](./Setup-Guide.md) | Environment setup and first-run checklist. |
| [Glossary.md](./Glossary.md) | Definitions of key ETL and analytics terms. |
| [Team-Roles.md](./Team-Roles.md) | Compatibility page pointing to merged role sections. |

## Quick Rules

1. Put source input files in `data/raw/`.
2. Keep rejected records in `data/rejected/` and temporary problem files in `data/quarantine/`.
3. Keep transformed output in `data/clean/`.
4. Save each SQL change as a new numbered script in `sql/scripts/`.
5. Export ADF JSON assets into `adf/` folders.
6. Update both [Project Flow](./project_flow.md) and [Contributing](./Contributing.md) when role ownership or process changes.

