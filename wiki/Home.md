# Home - Customer Data ETL Wiki

Welcome to the official wiki for the **Customer Data ETL** project.

Whether you are a new team member joining mid-project or a student trying to understand data engineering for the first time, this wiki will walk you through everything -- from what ETL is, to how to run the pipeline yourself.

---

## What Is This Project?

**Customer Data ETL** is a data engineering pipeline that reads raw customer records from a **CRM system exported to six CSV files** and automatically:

1. **Extracts** the data from those source files
2. **Transforms** it (cleans, standardizes, validates)
3. **Loads** it into a clean, analysis-ready PostgreSQL database

The result is a single, reliable source of customer data that a BI analyst or reporting tool can query directly.

---

## Why Do ETL Pipelines Matter?

In the real world, customer data is rarely clean or centralized. It lives in many places -- CRM systems, databases, spreadsheets -- and each source uses different formats, column names, and quality standards.

Without an ETL pipeline:
- Analysts waste hours manually cleaning data
- Reports show inconsistent numbers because each team queries a different source
- Duplicate or missing records cause business decisions to be based on wrong data

An ETL pipeline solves this by **automating the journey from raw, messy data to clean, trusted data**, reliably and repeatably.

---

## What Problem Does This Project Solve?

This project integrates six customer data entities that use different formats and naming conventions. The pipeline:

- Normalises column names, date formats, phone formats, and text casing
- Validates referential integrity across all tables
- Quarantines duplicates (email, SKU) and rows with bad references
- Loads the result into PostgreSQL for downstream analytics

---

## Project Workflow and Timeline

The project follows a practical flow from source understanding to validated delivery:

1. Understand source context and business goals
2. Explore data characteristics and edge cases
3. Define architecture and ETL approach
4. Execute extraction, transformation, and load iterations
5. Validate output quality and resolve issues
6. Publish documentation and final reporting outputs

### Delivery Timeline

| Phase | Focus |
|---|---|
| Week 1 | Source exploration and architecture setup |
| Week 2 | Pipeline implementation and initial runs |
| Week 3 | Modeling refinements and validation hardening |
| Week 4 | Final documentation, sign-off checks, and presentation prep |

---

## High-Level Architecture

```
data/raw/       Python ETL Pipeline       PostgreSQL
  contacts.csv  ┌──────────────────┐      crm_db
  customers.csv │ extract          │      ├── contact
  products.csv  │ transform        │      ├── customer
  sales_orders  │ validate         │      ├── product
  order_lines   │ load             │      ├── sales_order
  etl_batch     │ reconcile        │      └── order_line
                └──────────────────┘
```

The Python ETL pipeline orchestrates the full workflow: it reads source CSVs, applies cleaning and validation rules, writes clean/quarantine/rejected CSVs, then loads into PostgreSQL staging and gold tables.

---

## Tech Stack

| Tool | Role |
|---|---|
| **Python** | ETL pipeline -- extract, transform, validate, load, reconcile |
| **PostgreSQL** | Target database (`crm_db`) |
| **CSV** | Source data format |
| **Git / GitHub** | Version control, wiki, PR templates |

---

## Repository Structure

```
CAI4_AIS5_S11_P2/
├── data/
│   ├── raw/              ← Source CSV files (never edit)
│   ├── clean/            ← Pipeline writes processed output here
│   ├── rejected/         ← Rows that failed validation
│   └── quarantine/       ← Recoverable but suspicious rows
├── etl/                  ← Python ETL pipeline
│   ├── main.py           ← Orchestrator
│   ├── extract.py        ← Reads data/raw/
│   ├── transform.py      ← Cleans and normalises
│   ├── validate.py       ← Quality checks
│   ├── load.py           ← Loads to PostgreSQL
│   ├── reconcile.py      ← Verifies row counts
│   ├── config.py         ← Configuration
│   ├── utils/            ← DB and logging utilities
│   └── logs/             ← Per-run log files
├── scripts/sql/scripts/  ← Numbered SQL scripts
├── wiki/                 ← This wiki
├── presentation/         ← Demo slides and screenshots
└── .github/              ← Issue templates, PR template, CI/CD
```

---

## Wiki Navigation

| Page | What you will learn |
|---|---|
| [Home](./Home.md) | Project overview, architecture, and this navigation guide |
| [Run Guide](./Run-Guide.md) | Clone the repo and configure your environment step by step |
| [Data Sources](./Data-Sources.md) | Source CSV schemas, formats, and quality issues |
| [Transformation Rules](./Transformation-Rules.md) | Cleaning, validation rules, dedup logic, FK cascade rules |
| [Data Quality Definitions](./Data-Quality-Definitions.md) | Rejected vs Quarantine vs Clean -- what each tier means |
| [Project Architecture](./Project-Architecture.md) | Deep dive into each layer of the pipeline |
| [ETL Pipeline](./ETL-Pipeline.md) | How the pipeline works end to end |
| [Glossary](./Glossary.md) | Plain-English definitions of every technical term used here |
| [Team Roles](./Team-Roles.md) | Team member roles and responsibilities |

---

## Team Members

| Name | Role | GitHub |
|---|---|---|
| Ali | Project Lead / Architecture | @Ali-Hegazy-Ai |
| Amin | ETL / ADF Pipeline | TBD |
| Mennat Allah | Data Modeling / SQL | TBD |
| Aseel | Data Validation / Testing | TBD |
| Habiba | Documentation / BI | TBD |

---

> **New to ETL?** Start with the [Glossary](./Glossary.md) to learn the key terms, then read [Project Architecture](./Project-Architecture.md) to see the big picture before diving into technical details.
