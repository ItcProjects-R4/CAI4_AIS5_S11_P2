# ETL لبيانات العملاء من مصادر متعددة
# Customer Data ETL - Multiple Sources Integration

**Project Goal**: Integrate customer data from CRM and Excel sources, transform, and prepare for analysis in Data Warehouse.

**Technologies**: Azure Data Factory, SQL Server, Data Flows, Python

**Expected Output**: Customer Data Warehouse ready for analytics and Power BI dashboards.

## Team Structure

| Role | Member | Tasks |
|------|--------|-------|
| Data Extraction | Member 1 | استخراج البيانات من CRM و Excel |
| Data Cleaning | Member 2 | تنظيف وتحويل البيانات |
| Data Modeling | Member 3 | تصميم Schema و Data Warehouse |
| Data Validation | Member 4 | التحقق من جودة البيانات |
| Documentation | Member 5 | توثيق و Power BI Dashboard |

## Project Structure

```
├── member1_extraction/    # Data extraction sources
├── member2_cleaning/      # Data transformation scripts
├── member3_modeling/      # Schema and warehouse design
├── member4_validation/    # QA and testing
├── member5_documentation/ # Reports and dashboards
├── data/                  # SQL schemas
├── docker/                # Container setup
└── src/                   # Utilities
```
