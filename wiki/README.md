# Wiki README

This file is the index for all markdown documentation in `wiki/`.

## Core Entry Points

- [Home](./Home.md)
- [Run Guide](./Run-Guide.md)
- [Data Sources](./Data-Sources.md)

## All Wiki Markdown Files

| File | Purpose |
|---|---|
| [README.md](./README.md) | Wiki index and quick navigation. |
| [Home.md](./Home.md) | Main project overview and wiki navigation. |
| [project_flow.md](./project_flow.md) | Planning flow, role knowledge, deliverables, and timeline. |
| [Run-Guide.md](./Run-Guide.md) | Environment setup, prerequisites, and first-run steps. |
| [Data-Sources.md](./Data-Sources.md) | Source systems, fields, and ingestion context. |
| [Transformation-Rules.md](./Transformation-Rules.md) | Cleaning, validation, and business rules. |
| [Data-Quality-Definitions.md](./Data-Quality-Definitions.md) | Definitions of Clean, Rejected, and Quarantine tiers. |
| [Project-Architecture.md](./Project-Architecture.md) | Architecture layers and design rationale. |
| [ETL-Pipeline.md](./ETL-Pipeline.md) | Pipeline behavior and execution notes. |
| [Glossary.md](./Glossary.md) | Definitions of key ETL and analytics terms. |
| [Team-Roles.md](./Team-Roles.md) | Team member roles and responsibilities. |

## Quick Rules

1. Place source input files in `data/raw/`.
2. Keep rejected records in `data/rejected/` and temporary problem files in `data/quarantine/`.
3. Keep transformed output in `data/clean/`.
4. Save each SQL change as a new numbered script in `scripts/sql/scripts/`.
5. Update both [Project Flow](./project_flow.md) and this wiki when project structures or processes change.
