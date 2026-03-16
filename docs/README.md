# ETL for Customer Data from Multiple Sources



## Project Goal
Merge customer data from CRM and Excel, clean/transform it, and load clean output that is ready for Data Warehouse analysis.

## Tech Stack
- Azure Data Factory
- SQL Server
- Data Flows

## Project Folder Map

Use only these folders:

```
customer-data-etl/
├── data/
│   ├── raw/      # Original source files (CRM export, Excel)
│   └── clean/    # Final cleaned files ready for analysis
├── sql/
│   └── scripts/  # SQL scripts for tables/views/load steps
├── adf/
│   ├── pipelines/        # ADF pipelines
│   ├── datasets/         # ADF datasets
│   └── linked_services/  # ADF connections
└── docs/
		├── README.md         # This file
		└── project_flow.md   # Team phases and workflow
```

## Quick Working Rules (Student Version)
1. Put source input files in `data/raw/`.
2. Keep transformed output in `data/clean/`.
3. Save every SQL change as a new script in `sql/scripts/`.
4. Save/export ADF JSON assets into `adf/` folders.
5. Track owners, weekly phases, and progress in `docs/project_flow.md`.

## Documentation Split (No Overlap)
- `docs/README.md` (this file): project goal, stack, folder map, and baseline working rules.
- `docs/project_flow.md`: team role ownership, iterative week-by-week workflow, cycle tracker, and delivery status.

## Expected Output
Clean customer dataset ready for analysis in Data Warehouse/BI reporting.
