# Project Flow & Timeline

## ETL لبيانات العملاء من مصادر متعددة
## Customer Data ETL - Multiple Sources

---

## Project Phases Timeline

### Phase 01: Requirements & Planning
**Reference**: `./phases/phase_01_requirements/`

- Define business requirements
- Identify data sources (CRM, Excel)
- Document data quality standards
- Plan team structure

---

### Phase 02: Source Analysis
**Reference**: `./phases/phase_02_source_analysis/`

- Analyze CRM data structure
- Analyze Excel data format
- Document source specifications
- Identify data mapping rules

---

### Phase 03: Schema Design
**Reference**: `./phases/phase_03_schema_design/`

- Design staging tables
- Design dimensional tables
- Design fact tables
- Create ER diagrams
- SQL scripts in `./sql/`

---

### Phase 04: ETL Development
**Reference**: `./phases/phase_04_etl_development/`

- Develop extraction logic
- Develop transformation logic
- Develop loading logic
- Azure Data Factory pipelines in `./adf/`
- Python code in `./src/`

---

### Phase 05: Testing & Validation
**Reference**: `./phases/phase_05_testing/`

- Unit testing
- Integration testing
- Data quality testing
- Performance testing
- Test files in `./tests/`

---

### Phase 06: Deployment & Operations
**Reference**: `./phases/phase_06_deployment/`

- Infrastructure deployment (`./infra/`)
- Production configuration (`./config/prod/`)
- Documentation (`./docs/`)
- Run books and operations guide

---

## Project Structure

```
root/
├── phases/                     (Phase workspaces)
│   ├── phase_01_requirements/
│   ├── phase_02_source_analysis/
│   ├── phase_03_schema_design/
│   ├── phase_04_etl_development/
│   ├── phase_05_testing/
│   └── phase_06_deployment/
│
├── src/                        (Python code)
├── sql/                        (SQL scripts)
├── adf/                        (Azure Data Factory)
├── data/                       (Data layers)
├── docs/                       (Documentation)
├── infra/                      (Infrastructure)
├── tests/                      (Test suite)
├── scripts/                    (Automation)
├── config/                     (Configurations)
└── PROJECT_FLOW.md            (This file)
```

---

## Progress Tracking

| Phase | Status | Owner | Start Date | End Date |
|-------|--------|-------|-----------|----------|
| Phase 01 | 🔵 Pending | - | - | - |
| Phase 02 | 🔵 Pending | - | - | - |
| Phase 03 | 🔵 Pending | - | - | - |
| Phase 04 | 🔵 Pending | - | - | - |
| Phase 05 | 🔵 Pending | - | - | - |
| Phase 06 | 🔵 Pending | - | - | - |

---

## Team Roles

| Role | Phase | Member |
|------|-------|--------|
| 🔹 Data Extraction | Phase 02, 04 | - |
| 🔹 Data Cleaning | Phase 04 | - |
| 🔹 Data Modeling | Phase 03 | - |
| 🔹 Data Validation | Phase 05 | - |
| 🔹 Documentation | Phase 01, 06 | - |

---

**Start Date**: [TBD]  
**Target Completion**: [TBD]  
**Git Repository**: https://github.com/Ali-Hegazy-Ai/customer-data-etl
