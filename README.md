# Customer Data ETL

Local project scaffold for a customer ETL pipeline that:
- Extracts customer data from CRM exports and Excel files
- Transforms data using Azure Data Factory Data Flows
- Loads data into Azure SQL Data Warehouse patterns (staging, core, marts)

## Exact Folder Hierarchy

```text
customer-data-etl/
├── adf/
│   ├── source/
│   │   ├── dataset/
│   │   ├── dataflow/
│   │   ├── factory/
│   │   ├── globalParameters/
│   │   ├── integrationRuntime/
│   │   ├── linkedService/
│   │   ├── managedVirtualNetwork/
│   │   ├── pipeline/
│   │   └── trigger/
│   ├── arm_templates/
│   │   ├── dev/
│   │   ├── test/
│   │   └── prod/
│   └── README.md
├── config/
│   ├── dev/
│   ├── test/
│   └── prod/
├── data/
│   ├── sample/
│   │   ├── crm/
│   │   ├── excel/
│   │   └── reference/
│   ├── raw/
│   │   ├── crm/
│   │   └── excel/
│   ├── staging/
│   ├── curated/
│   ├── rejected/
│   └── archive/
├── docs/
│   ├── architecture/
│   ├── data-dictionary/
│   ├── mapping/
│   ├── runbooks/
│   └── setup/
├── infra/
│   ├── bicep/
│   ├── parameters/
│   └── policies/
├── scripts/
│   ├── bootstrap/
│   ├── validation/
│   └── release/
├── sql/
│   ├── 00_admin/
│   ├── 01_schemas/
│   ├── 02_staging/
│   ├── 03_core/
│   ├── 04_marts/
│   ├── 05_views/
│   ├── 06_procedures/
│   ├── 07_security/
│   ├── 08_validation/
│   └── 99_rollback/
├── src/
│   ├── connectors/
│   ├── transformations/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data-quality/
├── .env.example
└── README.md
```

## Environment Setup Guide

Follow: `docs/setup/local-environment.md`

## Quick Start

1. Create and activate virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Initialize local folders and `.env`:
   ```bash
   bash scripts/bootstrap/init_local.sh
   ```
3. Validate project structure:
   ```bash
   bash scripts/validation/validate_structure.sh
   ```
4. Update `.env` with Azure and SQL values.
5. Run SQL scripts in order from `sql/00_admin` to `sql/08_validation`.

