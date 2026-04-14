# ETL for Customer Data from Multiple Sources

Beginner-friendly college group project to integrate CRM and Excel customer data, transform it, and prepare it for analysis.

## Start Here
- Working guide: [docs/README.md](docs/README.md)
- Full wiki: [wiki/Home.md](wiki/Home.md)
- Weekly progress: [docs/project_flow.md](docs/project_flow.md)

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

## Notes
- `wiki/` is the canonical project documentation.
- The root-level files `architecture.md`, `extraction_strategy.md`, `raw_layer_rules.md`, and `sources_catalog.md` are retained as reference notes.
