# Local Environment Setup (ADF + Azure SQL)

This guide sets up a local developer environment for the customer ETL project.

## 1. Prerequisites

Install the following:
- Python 3.11+ (`python3 --version`)
- Azure CLI (`az --version`)
- `sqlcmd` client (`sqlcmd -?`)
- Azure Data Factory Studio access (for authoring/publishing ADF assets)
- Optional: Visual Studio Code + SQL tools extension

## 2. Clone and Prepare Python Environment

```bash
git clone <your-repository-url>
cd customer-data-etl
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. Configure Environment Variables

Copy `.env.example` and update values:

```bash
cp .env.example .env
```

Required variables:
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_LOCATION`
- `AZURE_DATA_FACTORY_NAME`
- `AZURE_SQL_SERVER`
- `AZURE_SQL_DATABASE`
- `AZURE_SQL_USER`
- `AZURE_SQL_PASSWORD`

## 4. Authenticate to Azure

```bash
az login
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
```

## 5. Initialize Local Directories

```bash
bash scripts/bootstrap/init_local.sh
bash scripts/validation/validate_structure.sh
```

## 6. SQL Warehouse Setup

Run scripts in this order:
1. `sql/00_admin`
2. `sql/01_schemas`
3. `sql/02_staging`
4. `sql/03_core`
5. `sql/04_marts`
6. `sql/05_views`
7. `sql/06_procedures`
8. `sql/07_security`
9. `sql/08_validation`

Example command:

```bash
sqlcmd \
  -S "$AZURE_SQL_SERVER" \
  -d "$AZURE_SQL_DATABASE" \
  -U "$AZURE_SQL_USER" \
  -P "$AZURE_SQL_PASSWORD" \
  -i sql/01_schemas/001_create_schemas.sql
```

## 7. ADF Source and ARM Template Workflow

- Author ADF JSON assets under `adf/source/*` (datasets, pipelines, dataflows, etc.).
- Store published ARM templates in:
  - `adf/arm_templates/dev`
  - `adf/arm_templates/test`
  - `adf/arm_templates/prod`
- Keep environment-specific parameters in each environment directory.

Recommended ADF release flow:
1. Develop and test in ADF Dev factory.
2. Publish ADF changes and export/update ARM templates in `adf/arm_templates/dev`.
3. Promote by updating parameter files in `test` and `prod`.

## 8. Data Handling Conventions

- `data/sample`: Small version-controlled samples for development and tests
- `data/raw`: Landing area for CRM and Excel extracts (ignored by git)
- `data/staging`: Intermediate local extracts (ignored by git)
- `data/curated`: Cleaned local outputs (ignored by git)
- `data/rejected`: Invalid records and DQ failures (ignored by git)
- `data/archive`: Archived local snapshots (ignored by git)

## 9. Recommended Working Pattern

1. Place source extracts under `data/raw/crm` and `data/raw/excel`.
2. Validate mapping and quality rules from `docs/mapping` and `sql/08_validation`.
3. Push staging loads to Azure SQL via ADF copy activities.
4. Apply transformation logic via Data Flows and SQL procedures.
5. Validate dimensional/mart outputs before publishing downstream.

