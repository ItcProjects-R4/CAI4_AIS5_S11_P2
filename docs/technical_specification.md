# ETL Technical Specification — Customer Data Pipeline

**Version:** 1.0  
**Date:** 2024-06-01  
**Status:** Implementation-Ready  
**Authors:** ETL Team (Ali, Amin, Mennat Allah, Aseel, Habiba)

---

## Table of Contents

1. [Source System Specifications](#1-source-system-specifications)
2. [Raw Layer Design (Azure Blob)](#2-raw-layer-design-azure-blob)
3. [Transformation Specification](#3-transformation-specification)
4. [Curated Data Model (SQL)](#4-curated-data-model-sql)
5. [ADF Pipeline Design](#5-adf-pipeline-design)
6. [Data Quality Rules](#6-data-quality-rules)
7. [SQL Scripts](#7-sql-scripts)
8. [Analytics Layer](#8-analytics-layer)

---

## 1. Source System Specifications

### 1.1 Source 1 — CRM Export (CSV)

**System:** Internal CRM platform  
**Format:** CSV (UTF-8, comma-delimited, double-quote escape, CRLF or LF line endings)  
**Delivery:** Manual file drop to Azure Blob Storage `data/raw/` weekly  
**File naming:** `crm_customers_YYYYMMDD.csv`  
**Example file:** `crm_customers_20240601.csv`

#### Schema

| Field | Type | Nullable | Description |
|---|---|---|---|
| `customer_id` | String (Integer-compatible) | No | Unique customer identifier. Must cast to INT. |
| `full_name` | String | No | Customer full name. May have leading/trailing spaces. Mixed casing. |
| `email` | String | Yes | Contact email. Mixed casing. May be blank. |
| `phone` | String | Yes | Local phone number. Formats vary: `01012345678`, `010-9876-5432`, `+20 100 111 2222`. No consistent country code. |
| `signup_date` | String | Yes | Registration date string. Format: `YYYY-MM-DD`. Blank for records imported before 2022. |
| `country` | String | Yes | Full country name in English (`Egypt`, `Saudi Arabia`). |
| `segment` | String | Yes | Customer tier. Values: `Premium`, `premium`, `PREMIUM`, `Standard`, `standard`, `STANDARD`, `Basic`, `basic`, `BASIC`. |

#### Example Record

```
customer_id,full_name,email,phone,signup_date,country,segment
1001,John Doe,john@example.com,01012345678,2023-05-10,Egypt,Premium
1005,Mohamed Ibrahim,m.ibrahim@corp.com,01156789012,,Egypt,Standard
```

#### Known Issues

| Issue | Severity | ETL Handling |
|---|---|---|
| `phone` has inconsistent formats (spaces, dashes, no country code, local prefix `0`) | High | Normalise to `+20-XXX-XXXXXXX` for Egyptian numbers via regex in Derived Column |
| `signup_date` blank for pre-2022 records | Medium | Coerce to NULL; documented exception |
| `segment` mixed casing | Medium | Convert to `UPPER()` in Derived Column |
| Duplicate `customer_id` in incremental exports | High | Deduplicate in Aggregate step, CRM record preferred |
| Leading/trailing spaces in `full_name` | Low | `trim(initCap())` in Derived Column |

---

### 1.2 Source 2 — Excel Spreadsheet

**System:** Sales team Excel workbook  
**Format:** Microsoft Excel Open XML (`.xlsx`)  
**Delivery:** Manual file drop to Azure Blob Storage `data/raw/` weekly  
**File naming:** `excel_customers_YYYYMMDD.xlsx`  
**Example file:** `excel_customers_20240601.xlsx`  
**Sheet:** `Customers` (always first sheet, row 1 = header)

#### Schema

| Field | Type | Nullable | Description |
|---|---|---|---|
| `CustomerID` | String (Integer-compatible) | No | Unique customer identifier. Must cast to INT. |
| `Name` | String | No | Customer full name. Mixed casing. |
| `EmailAddress` | String | Yes | Contact email. Mixed case (e.g. `John@Example.COM`). |
| `PhoneNumber` | String | Yes | Phone with country code prefix: `+20-101-2345678`. May contain spaces. |
| `JoinDate` | String or Excel serial | Yes | Date joined. Either `DD/MM/YYYY` string or an Excel date serial number (e.g. `45048`). Blank where missing. |
| `Country` | String | Yes | ISO 3166-1 alpha-3 country code: `EGY`, `SAU`, `ARE`, `JOR`, `KWT`. |
| `CustomerSegment` | String | Yes | Customer tier. Uppercase: `PREMIUM`, `STANDARD`, `BASIC`. |

#### Example Record

```
CustomerID,Name,EmailAddress,PhoneNumber,JoinDate,Country,CustomerSegment
1001,John Doe,John@Example.COM,+20-101-2345678,10/05/2023,EGY,PREMIUM
1005,Mohamed Ibrahim,M.Ibrahim@Corp.com,+20-115-6789012,,EGY,STANDARD
```

#### Known Issues

| Issue | Severity | ETL Handling |
|---|---|---|
| `JoinDate` stored as Excel serial number (e.g. `45048`) | High | Detect integer value > 40000, convert via `addDays('1899-12-30', serial)` |
| `Country` uses ISO 3-letter codes, not full names | High | Map via lookup table in Derived Column (see Section 3.5) |
| `EmailAddress` is mixed case | Medium | `lower(trim())` in Derived Column |
| Merged cells produce blank rows (null `CustomerID`) | Medium | Dropped by Filter step |
| `CustomerID` may overlap with CRM IDs | High | Resolved by Aggregate deduplication; CRM preferred |

---

## 2. Raw Layer Design (Azure Blob)

### 2.1 Storage Account

| Property | Value |
|---|---|
| Service | Azure Blob Storage |
| Container | `customer-data-etl` |
| Access tier | Hot |
| Redundancy | LRS (minimum); GRS recommended for production |

### 2.2 Folder Structure

```
customer-data-etl/                        <- Blob container root
├── data/
│   ├── raw/                              <- Original source files. Never modified after drop.
│   │   ├── crm_customers_YYYYMMDD.csv
│   │   └── excel_customers_YYYYMMDD.xlsx
│   ├── clean/                            <- Clean output files written by ADF after each run.
│   │   └── customers_clean_YYYYMMDD.csv
│   └── rejected/                         <- Rows rejected by Filter step.
│       └── rejected_YYYYMMDD.csv
└── adf-staging/                          <- Temporary staging area for ADF Data Flow Spark cluster.
    └── (managed by ADF; do not edit manually)
```

### 2.3 File Naming Convention

| File Type | Pattern | Example |
|---|---|---|
| CRM source | `crm_customers_YYYYMMDD.csv` | `crm_customers_20240601.csv` |
| Excel source | `excel_customers_YYYYMMDD.xlsx` | `excel_customers_20240601.xlsx` |
| Clean output | `customers_clean_YYYYMMDD.csv` | `customers_clean_20240601.csv` |
| Rejected rows | `rejected_YYYYMMDD.csv` | `rejected_20240601.csv` |

`YYYYMMDD` is the pipeline `RunDate` parameter, formatted as `formatDateTime(pipeline().parameters.RunDate, 'yyyyMMdd')`.

### 2.4 Partitioning

Raw and clean files are partitioned **by run date** using the file name suffix. Each pipeline run writes its own dated file. Previous files are retained for audit. Files older than 90 days should be moved to Archive tier (Cool or Cold) via a lifecycle management policy.

Clean CSV columns (output schema):

| Column | Type | Example |
|---|---|---|
| `CustomerID` | String | `1001` |
| `CustomerName` | String | `John Doe` |
| `Email` | String | `john@example.com` |
| `Phone` | String | `+20-101-2345678` |
| `SignupDate` | String (ISO date) | `2023-05-10` |
| `Country` | String | `Egypt` |
| `Segment` | String | `PREMIUM` |
| `SourceSystem` | String | `CRM` |

---

## 3. Transformation Specification

### 3.1 Column Mapping (Source → Target)

#### CRM → Unified Schema

| Source Field (`crm_customers_*.csv`) | Target Field (unified) | Transformation Applied |
|---|---|---|
| `customer_id` | `CustomerID` | `toInteger(customer_id)` |
| `full_name` | `CustomerName` | `trim(initCap(full_name))` |
| `email` | `Email` | `lower(trim(email))` |
| `phone` | `Phone` | Regex normalisation — see Section 3.4 |
| `signup_date` | `SignupDate` | `toDate(signup_date, 'yyyy-MM-dd')` or NULL if blank |
| `country` | `Country` | Full-name passthrough — see Section 3.5 |
| `segment` | `Segment` | `upper(trim(segment))` |
| *(hardcoded)* | `SourceSystem` | `'CRM'` |

#### Excel → Unified Schema

| Source Field (`excel_customers_*.xlsx`) | Target Field (unified) | Transformation Applied |
|---|---|---|
| `CustomerID` | `CustomerID` | `toInteger(CustomerID)` |
| `Name` | `CustomerName` | `trim(initCap(Name))` |
| `EmailAddress` | `Email` | `lower(trim(EmailAddress))` |
| `PhoneNumber` | `Phone` | `regexReplace(trim(PhoneNumber), '[\s]', '')` — spaces removed |
| `JoinDate` | `SignupDate` | If value > 40000 → Excel serial conversion; else `toDate(JoinDate, 'dd/MM/yyyy')` |
| `Country` | `Country` | ISO-3 code mapped to full name — see Section 3.5 |
| `CustomerSegment` | `Segment` | `upper(trim(CustomerSegment))` |
| *(hardcoded)* | `SourceSystem` | `'Excel'` |

---

### 3.2 Deduplication Logic

**Scope:** Duplicates within a single source file AND across both sources.

**Step 1 — Within-source deduplication (ADF Filter):**  
Both streams are filtered to remove rows where `CustomerID IS NULL` or `CustomerID = 0` before union. This prevents propagating unmatchable duplicates.

**Step 2 — Cross-source deduplication (ADF Aggregate):**  
After the Union step, records are grouped by `CustomerID`. Exactly one record is kept per `CustomerID` using the following priority rules, applied field by field:

```
first(FieldValue, SourceSystem == 'CRM')
```

This expression picks the CRM value if a CRM record exists for that `CustomerID`. If only an Excel record exists, the Excel value is used.

**Tie-breaking rule:** Within the same source (e.g. two CRM records with the same `CustomerID`), the SQL-side `usp_UpsertCustomers` procedure applies a secondary sort:

```sql
ROW_NUMBER() OVER (
    PARTITION BY CustomerID
    ORDER BY
        CASE WHEN SourceSystem = 'CRM' THEN 0 ELSE 1 END,
        LoadedAt DESC
) = 1
```

This keeps the most recently loaded record from the preferred source.

---

### 3.3 Identity Resolution

Customers are matched exclusively on `CustomerID` (integer). No fuzzy name or email matching is performed. If two records have the same `CustomerID`, they are considered the same customer. The CRM record is canonical.

If a customer appears with two different `CustomerID` values across sources (a broken key scenario), they will remain as two separate customers in `dbo.Customers`. This must be resolved at the source system level — not in the ETL pipeline.

---

### 3.4 Phone Normalisation Rules

**Goal:** Store phone numbers in `+XX-XXX-XXXXXXX` format.

**CRM phone — ADF Derived Column expression:**

```
regexReplace(
  regexReplace(trim(phone), '[\s\-\(\)]', ''),  -- strip spaces, dashes, parens
  '^(00|0)',                                      -- replace leading 00 or 0
  '+20'                                           -- with Egyptian country code
)
```

**Excel phone — ADF Derived Column expression:**

```
regexReplace(trim(PhoneNumber), '[\s]', '')  -- strip spaces only; +XX prefix already present
```

**Resulting format examples:**

| Raw Input | Normalised Output |
|---|---|
| `01012345678` | `+2001012345678` |
| `010-9876-5432` | `+20109876432` |
| `+20 100 111 2222` | `+201001112222` |
| `+20-101-2345678` | `+20-101-2345678` |

---

### 3.5 Country Code Mapping (ISO-3 to Full Name)

Applied in the Excel `DerivedExcel` step:

| ISO Code | Full Name |
|---|---|
| `EGY` | `Egypt` |
| `SAU` | `Saudi Arabia` |
| `ARE` | `United Arab Emirates` |
| `JOR` | `Jordan` |
| `KWT` | `Kuwait` |
| `USA` | `United States` |
| `GBR` | `United Kingdom` |
| `FRA` | `France` |
| `DEU` | `Germany` |
| *(any other)* | Pass through unchanged |

ADF Derived Column expression:

```
case(
  Country == 'EGY', 'Egypt',
  Country == 'SAU', 'Saudi Arabia',
  Country == 'ARE', 'United Arab Emirates',
  Country == 'JOR', 'Jordan',
  Country == 'KWT', 'Kuwait',
  Country == 'USA', 'United States',
  Country == 'GBR', 'United Kingdom',
  Country == 'FRA', 'France',
  Country == 'DEU', 'Germany',
  Country
)
```

---

### 3.6 Null Handling Rules

| Field | Null Allowed? | Rule |
|---|---|---|
| `CustomerID` | **No** | Rows with null or zero `CustomerID` are rejected to `data/rejected/`. |
| `CustomerName` | **No** | Rows with null or blank (after trim) `CustomerName` are rejected to `data/rejected/`. |
| `Email` | Yes | NULL is stored. No default value. |
| `Phone` | Yes | NULL is stored. No default value. |
| `SignupDate` | Yes | NULL for pre-2022 CRM imports. Documented exception. |
| `Country` | Yes | NULL is stored if source field is blank. |
| `Segment` | Yes | NULL is stored if source field is blank. |
| `SourceSystem` | **No** | Always hardcoded to `'CRM'` or `'Excel'`. Never NULL. |

---

### 3.7 Data Standardisation Rules

| Field | Standard Applied |
|---|---|
| `CustomerName` | Title case (`initCap`), leading/trailing spaces trimmed |
| `Email` | Lowercase, leading/trailing spaces trimmed |
| `Phone` | Spaces, dashes, parentheses removed; Egyptian local numbers prefixed with `+20` |
| `SignupDate` | ISO 8601 `DATE` type (`YYYY-MM-DD`). Excel serial numbers converted via epoch arithmetic |
| `Country` | Full English country name (ISO 3166-1 alpha-2 name style). ISO-3 codes replaced via lookup |
| `Segment` | Uppercase: `PREMIUM`, `STANDARD`, or `BASIC` only |
| `SourceSystem` | Exactly `'CRM'` or `'Excel'` — no other values |

---

## 4. Curated Data Model (SQL)

**Database:** `CustomerDW`  
**SQL Server version:** SQL Server 2019 / Azure SQL Database  
**Default schema:** `dbo`  
**Collation:** `SQL_Latin1_General_CP1_CI_AS`

### 4.1 Tables

#### dbo.Customers

The main table holding final, clean, deduplicated customer records after each pipeline run.

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| `CustomerID` | `INT` | NOT NULL | PK | Unique customer identifier from source systems |
| `CustomerName` | `NVARCHAR(200)` | NOT NULL | — | Full name, title-cased, trimmed |
| `Email` | `NVARCHAR(255)` | NULL | — | Email address, lowercase |
| `Phone` | `NVARCHAR(50)` | NULL | — | Normalised phone number in `+XX-XXX-XXXXXXX` format |
| `SignupDate` | `DATE` | NULL | — | Date customer registered (NULL allowed for pre-2022 imports) |
| `Country` | `NVARCHAR(100)` | NULL | — | Full English country name |
| `Segment` | `NVARCHAR(50)` | NULL | — | Customer tier: `PREMIUM`, `STANDARD`, or `BASIC` |
| `SourceSystem` | `NVARCHAR(20)` | NULL | — | Origin of the winning record: `CRM` or `Excel` |
| `LoadedAt` | `DATETIME2(0)` | NOT NULL | — | UTC timestamp of last load/update |

**Constraints:** `CONSTRAINT PK_Customers PRIMARY KEY (CustomerID)`

---

#### dbo.CustomerStaging

Temporary buffer table. ADF Data Flow writes here first; `usp_UpsertCustomers` merges into `dbo.Customers` and then truncates this table.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `CustomerID` | `INT` | NULL | Allows NULLs for bulk-load compatibility |
| `CustomerName` | `NVARCHAR(200)` | NULL | — |
| `Email` | `NVARCHAR(255)` | NULL | — |
| `Phone` | `NVARCHAR(50)` | NULL | — |
| `SignupDate` | `DATE` | NULL | — |
| `Country` | `NVARCHAR(100)` | NULL | — |
| `Segment` | `NVARCHAR(50)` | NULL | — |
| `SourceSystem` | `NVARCHAR(20)` | NULL | — |
| `LoadedAt` | `DATETIME2(0)` | NULL | — |

**No primary key** — intentional for bulk-load performance.

---

#### dbo.RejectedRecords

Stores rows that failed validation (null `CustomerID` or blank `CustomerName`) for investigation.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `RejectionID` | `INT IDENTITY(1,1)` | NOT NULL (PK) | Auto-increment identifier |
| `SourceSystem` | `NVARCHAR(20)` | NULL | `CRM` or `Excel` |
| `RawCustomerID` | `NVARCHAR(50)` | NULL | Original raw value (may be blank or non-numeric) |
| `RawName` | `NVARCHAR(500)` | NULL | Original raw name value |
| `RawEmail` | `NVARCHAR(500)` | NULL | Original raw email value |
| `RawPhone` | `NVARCHAR(100)` | NULL | Original raw phone value |
| `RawSignupDate` | `NVARCHAR(100)` | NULL | Original raw date string |
| `RawCountry` | `NVARCHAR(200)` | NULL | Original raw country value |
| `RawSegment` | `NVARCHAR(100)` | NULL | Original raw segment value |
| `RejectionReason` | `NVARCHAR(500)` | NOT NULL | Exact reason: `NULL_CUSTOMER_ID` or `BLANK_CUSTOMER_NAME` |
| `RejectedAt` | `DATETIME2(0)` | NOT NULL | UTC timestamp of rejection |

---

#### dbo.ETLRunLog

Audit log recording the outcome of every pipeline run.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `RunID` | `INT IDENTITY(1,1)` | NOT NULL (PK) | Auto-increment run identifier |
| `PipelineName` | `NVARCHAR(100)` | NOT NULL | Always `pl_customer_etl` |
| `RunStart` | `DATETIME2(0)` | NOT NULL | UTC start timestamp |
| `RunEnd` | `DATETIME2(0)` | NULL | UTC end timestamp (NULL while running) |
| `RowsLoaded` | `INT` | NULL | Count of rows successfully upserted into `dbo.Customers` |
| `RowsRejected` | `INT` | NULL | Count of rows written to `dbo.RejectedRecords` |
| `Status` | `NVARCHAR(20)` | NULL | `Running`, `Success`, or `Failed` |
| `Notes` | `NVARCHAR(MAX)` | NULL | Free-text notes or error messages |

---

### 4.2 Views

| View | Purpose |
|---|---|
| `dbo.vw_CustomerSummary` | Full customer list with derived `SignupYear` and `SignupMonth` columns for time-based slicing |
| `dbo.vw_CustomersBySegment` | Count of customers per segment |
| `dbo.vw_CustomersByCountry` | Count of customers per country |
| `dbo.vw_MonthlySignups` | Monthly new customer acquisition counts |
| `dbo.vw_ETLRunSummary` | Latest pipeline run statistics (top 1 by run start) |

---

### 4.3 ERD

```
dbo.Customers (PK: CustomerID)
    |
    | (no FK — ETLRunLog is independent of customer records)
    |
dbo.ETLRunLog (PK: RunID)

dbo.CustomerStaging
    --> merged into dbo.Customers via usp_UpsertCustomers
    --> truncated after each successful merge

dbo.RejectedRecords (PK: RejectionID)
    --> rows captured from ADF Data Flow Filter false branch
    --> no FK to Customers (rejected rows have no valid CustomerID)
```

**Relationships:**
- `dbo.CustomerStaging` → `dbo.Customers`: MERGE on `CustomerID` (no FK constraint; enforced procedurally)
- All other tables are independent; linked by `LoadedAt` timestamps and `RunID` for audit tracing

---

## 5. ADF Pipeline Design

**Pipeline name:** `pl_customer_etl`  
**Data Flow name:** `df_merge_transform`

### 5.1 Pipeline Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `RunDate` | String | `@formatDateTime(utcNow(), 'yyyy-MM-dd')` | Date used to construct source and output file names |

### 5.2 Pipeline Activities

```
LogPipelineStart ──> SetLogRunID
                          │
    ├──> ValidateCRMFileExists ──> IfCRMFileMissing ──(fail)──> FailMissingCRM
    │                                     │
    └──> ValidateExcelFileExists ──> IfExcelFileMissing ──(fail)──> FailMissingExcel
                                          │
                              (both success) ──> RunDataFlow
                                                     │
                                              UpsertToCustomers
                                             /                  \
                                     (success)                (failed/skipped)
                                         │                        │
                                 LogPipelineSuccess        LogPipelineFailure
```

### 5.3 Activity Details

#### Activity 1 — LogPipelineStart

| Property | Value |
|---|---|
| Type | `SqlServerStoredProcedure` |
| Procedure | `dbo.usp_LogETLRun` |
| Parameters | `PipelineName = 'pl_customer_etl'`, `Action = 'START'` |
| Timeout | 5 minutes |
| Retry | 1 (30-second interval) |
| On failure | Pipeline aborts; no run log entry updated |

---

#### Activity 2 — SetLogRunID

| Property | Value |
|---|---|
| Type | `SetVariable` |
| Variable | `LogRunID` |
| Value | `@activity('LogPipelineStart').output.firstRow.RunID` |
| Depends on | `LogPipelineStart (Succeeded)` |

---

#### Activity 3 — ValidateCRMFileExists

| Property | Value |
|---|---|
| Type | `GetMetadata` |
| Dataset | `ds_crm_source` |
| Fields | `['exists']` |
| Timeout | 2 minutes |
| Retry | 0 |
| Depends on | `SetLogRunID (Succeeded)` |

---

#### Activity 4 — ValidateExcelFileExists

| Property | Value |
|---|---|
| Type | `GetMetadata` |
| Dataset | `ds_excel_source` |
| Fields | `['exists']` |
| Timeout | 2 minutes |
| Retry | 0 |
| Depends on | `SetLogRunID (Succeeded)` |

---

#### Activity 5 — IfCRMFileMissing

| Property | Value |
|---|---|
| Type | `IfCondition` |
| Condition | `@equals(activity('ValidateCRMFileExists').output.exists, false)` |
| True branch | `Fail` activity with `errorCode = MISSING_CRM_FILE` and descriptive message |

---

#### Activity 6 — IfExcelFileMissing

| Property | Value |
|---|---|
| Type | `IfCondition` |
| Condition | `@equals(activity('ValidateExcelFileExists').output.exists, false)` |
| True branch | `Fail` activity with `errorCode = MISSING_EXCEL_FILE` and descriptive message |

---

#### Activity 7 — RunDataFlow

| Property | Value |
|---|---|
| Type | `ExecuteDataFlow` |
| Data Flow | `df_merge_transform` |
| Depends on | `IfCRMFileMissing (Succeeded)` AND `IfExcelFileMissing (Succeeded)` |
| Compute | 8 vCores, General purpose |
| Timeout | 1 hour |
| Retry | 1 (60-second interval) |

---

#### Activity 8 — UpsertToCustomers

| Property | Value |
|---|---|
| Type | `SqlServerStoredProcedure` |
| Procedure | `dbo.usp_UpsertCustomers` |
| Depends on | `RunDataFlow (Succeeded)` |
| Timeout | 30 minutes |
| Retry | 1 (30-second interval) |

---

#### Activity 9 — LogPipelineSuccess

| Property | Value |
|---|---|
| Type | `SqlServerStoredProcedure` |
| Procedure | `dbo.usp_LogETLRun` |
| Parameters | `Action = 'END'`, `Status = 'Success'`, `RunID = @variables('LogRunID')`, `RowsLoaded` from Data Flow metrics |
| Depends on | `UpsertToCustomers (Succeeded)` |

---

#### Activity 10 — LogPipelineFailure

| Property | Value |
|---|---|
| Type | `SqlServerStoredProcedure` |
| Procedure | `dbo.usp_LogETLRun` |
| Parameters | `Action = 'END'`, `Status = 'Failed'`, `RunID = @variables('LogRunID')`, `Notes = coalesce(RunDataFlow.error.message, UpsertToCustomers.error.message, 'Unknown error')` |
| Depends on | `RunDataFlow (Failed or Skipped)` AND `UpsertToCustomers (Failed or Skipped)` |

---

### 5.4 Data Flow Steps (df_merge_transform)

| Step | Name | Type | Inputs | Description |
|---|---|---|---|---|
| 1a | `SelectCRM` | Select | `CRMSource` | Rename `customer_id` → `CustomerID`, `full_name` → `CustomerName`, etc. |
| 1b | `SelectExcel` | Select | `ExcelSource` | Rename `CustomerID` stays, `Name` → `CustomerName`, `EmailAddress` → `Email`, etc. |
| 2a | `DerivedCRM` | DerivedColumn | `SelectCRM` | Cast, trim, lowercase, normalise phone, parse date, uppercase segment, set `SourceSystem = 'CRM'` |
| 2b | `DerivedExcel` | DerivedColumn | `SelectExcel` | Cast, trim, lowercase, convert Excel serial dates, map ISO country codes, set `SourceSystem = 'Excel'` |
| 3a | `FilterCRM` | Filter | `DerivedCRM` | Keep rows where `CustomerID != null && CustomerID > 0 && CustomerName != null && len(trim(CustomerName)) > 0` |
| 3b | `FilterExcel` | Filter | `DerivedExcel` | Same condition as FilterCRM |
| 4 | `UnionStreams` | Union | `FilterCRM`, `FilterExcel` | Append both streams; `unionAll = true` |
| 5 | `DeduplicateByCustomerID` | Aggregate | `UnionStreams` | Group by `CustomerID`; pick CRM values using `first(field, SourceSystem == 'CRM')` |
| 6a | `SinkCSV` | Sink | `DeduplicateByCustomerID` | Write to `ds_clean_output` (CSV in `data/clean/`) |
| 6b | `SinkSQL` | Sink | `DeduplicateByCustomerID` | Write to `ds_sql_customers` (`dbo.CustomerStaging`) with pre-SQL `TRUNCATE TABLE dbo.CustomerStaging` |

### 5.5 Triggers

| Trigger | Type | Schedule |
|---|---|---|
| `trg_weekly_monday` | Schedule | Every Monday at 06:00 UTC |
| `trg_on_file_arrival` | Storage Event (optional) | Fires when `crm_customers_*.csv` is created in `data/raw/` |

---

## 6. Data Quality Rules

### 6.1 Validation Rules

| Rule ID | Field | Rule | Expected Result | Severity |
|---|---|---|---|---|
| DQ-01 | — | `COUNT(*) FROM dbo.Customers > 0` | Row count > 0 | Critical |
| DQ-02 | `CustomerID` | `COUNT(*) WHERE CustomerID IS NULL = 0` | 0 | Critical |
| DQ-03 | `CustomerName` | `COUNT(*) WHERE CustomerName IS NULL OR LTRIM(RTRIM(CustomerName)) = '' = 0` | 0 | Critical |
| DQ-04 | `CustomerID` | No duplicate values: `HAVING COUNT(*) > 1` returns 0 rows | 0 rows | Critical |
| DQ-05 | `Email` | All non-null emails contain `@` and `.` AND equal `LOWER(Email)` | 0 violations | High |
| DQ-06 | `Segment` | Only `PREMIUM`, `STANDARD`, `BASIC`, or NULL | 0 invalid values | High |
| DQ-07 | `SignupDate` | No dates before `2000-01-01` or after today | 0 out-of-range | Medium |
| DQ-08 | `SourceSystem` | Only `CRM` or `Excel` | 0 invalid values | High |
| DQ-09 | `Country` | No 3-letter ISO codes (`LEN = 3 AND Country = UPPER(Country)`) | 0 rows | Medium |
| DQ-10 | `SourceSystem` | Both `CRM` and `Excel` present in load | Both counts > 0 | Medium |

### 6.2 SQL Validation Checks

See `sql/scripts/05_validation_queries.sql` for the complete set of implementation-ready SQL checks.

Critical checks (run-blocking — re-run pipeline if these fail):

```sql
-- DQ-02: Null CustomerID
SELECT COUNT(*) FROM dbo.Customers WHERE CustomerID IS NULL;
-- Must return 0

-- DQ-04: Duplicate CustomerID
SELECT CustomerID, COUNT(*) FROM dbo.Customers GROUP BY CustomerID HAVING COUNT(*) > 1;
-- Must return 0 rows

-- DQ-06: Invalid Segment
SELECT COUNT(*) FROM dbo.Customers
WHERE Segment IS NOT NULL AND Segment NOT IN ('PREMIUM', 'STANDARD', 'BASIC');
-- Must return 0
```

### 6.3 Reject Handling Strategy

1. **Capture:** The ADF Data Flow Filter step routes failing rows (null `CustomerID` or blank `CustomerName`) to a second Sink connected to the Filter false branch.
2. **Storage:** Rejected rows are written to `data/rejected/rejected_YYYYMMDD.csv` in Azure Blob Storage.
3. **Logging:** `dbo.RejectedRecords` table stores the raw field values and the exact `RejectionReason` code:
   - `NULL_CUSTOMER_ID` — `CustomerID` was null or zero after casting
   - `BLANK_CUSTOMER_NAME` — `CustomerName` was null or empty after trimming
4. **Review:** After each pipeline run, query `dbo.RejectedRecords` to identify patterns. The source file owner (CRM team or Sales team) must correct source data and re-export.
5. **Re-run:** After source correction, re-run the pipeline with the corrected file for the same `RunDate`.

---

## 7. SQL Scripts

### 7.1 File Reference

All scripts are in `sql/scripts/`. Run them in order on first setup.

| Script | Purpose |
|---|---|
| `01_create_database.sql` | Create `CustomerDW` database (run on `master`) |
| `02_create_tables.sql` | Create `Customers`, `CustomerStaging`, `RejectedRecords`, `ETLRunLog` |
| `03_create_views.sql` | Create reporting views |
| `04_load_procedures.sql` | Create `usp_UpsertCustomers` and `usp_LogETLRun` |
| `05_validation_queries.sql` | Quality-check queries — run after each pipeline execution |

All scripts are **idempotent**: safe to run more than once (use `IF NOT EXISTS` and `CREATE OR ALTER`).

### 7.2 CREATE TABLE Statements

#### dbo.Customers

```sql
CREATE TABLE dbo.Customers (
    CustomerID      INT             NOT NULL,
    CustomerName    NVARCHAR(200)   NOT NULL,
    Email           NVARCHAR(255)       NULL,
    Phone           NVARCHAR(50)        NULL,
    SignupDate      DATE                NULL,
    Country         NVARCHAR(100)       NULL,
    Segment         NVARCHAR(50)        NULL,
    SourceSystem    NVARCHAR(20)        NULL,
    LoadedAt        DATETIME2(0)    NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT PK_Customers PRIMARY KEY (CustomerID)
);
```

#### dbo.CustomerStaging

```sql
CREATE TABLE dbo.CustomerStaging (
    CustomerID      INT             NULL,
    CustomerName    NVARCHAR(200)   NULL,
    Email           NVARCHAR(255)   NULL,
    Phone           NVARCHAR(50)    NULL,
    SignupDate      DATE            NULL,
    Country         NVARCHAR(100)   NULL,
    Segment         NVARCHAR(50)    NULL,
    SourceSystem    NVARCHAR(20)    NULL,
    LoadedAt        DATETIME2(0)    NULL
);
```

#### dbo.ETLRunLog

```sql
CREATE TABLE dbo.ETLRunLog (
    RunID           INT             NOT NULL IDENTITY(1,1),
    PipelineName    NVARCHAR(100)   NOT NULL,
    RunStart        DATETIME2(0)    NOT NULL,
    RunEnd          DATETIME2(0)        NULL,
    RowsLoaded      INT                 NULL,
    RowsRejected    INT                 NULL,
    Status          NVARCHAR(20)        NULL,
    Notes           NVARCHAR(MAX)       NULL,
    CONSTRAINT PK_ETLRunLog PRIMARY KEY (RunID)
);
```

### 7.3 Key Transformation Queries

#### Upsert (MERGE) from Staging to Customers

```sql
MERGE dbo.Customers AS target
USING (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY CustomerID
        ORDER BY CASE WHEN SourceSystem = 'CRM' THEN 0 ELSE 1 END, LoadedAt DESC
    ) AS rn
    FROM dbo.CustomerStaging WHERE CustomerID IS NOT NULL
) AS source ON target.CustomerID = source.CustomerID AND source.rn = 1
WHEN MATCHED THEN
    UPDATE SET CustomerName = source.CustomerName, Email = source.Email,
               Phone = source.Phone, SignupDate = source.SignupDate,
               Country = source.Country, Segment = source.Segment,
               SourceSystem = source.SourceSystem, LoadedAt = GETUTCDATE()
WHEN NOT MATCHED BY TARGET THEN
    INSERT (CustomerID, CustomerName, Email, Phone, SignupDate, Country,
            Segment, SourceSystem, LoadedAt)
    VALUES (source.CustomerID, source.CustomerName, source.Email, source.Phone,
            source.SignupDate, source.Country, source.Segment,
            source.SourceSystem, GETUTCDATE());
```

#### Segment Distribution Report

```sql
SELECT Segment, COUNT(*) AS CustomerCount,
       CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS DECIMAL(5,2)) AS Percentage
FROM dbo.Customers
GROUP BY Segment
ORDER BY CustomerCount DESC;
```

#### Monthly Acquisition Trend

```sql
SELECT YEAR(SignupDate) AS SignupYear, MONTH(SignupDate) AS SignupMonth,
       COUNT(*) AS NewCustomers
FROM dbo.Customers
WHERE SignupDate IS NOT NULL
GROUP BY YEAR(SignupDate), MONTH(SignupDate)
ORDER BY SignupYear, SignupMonth;
```

---

## 8. Analytics Layer

### 8.1 Power BI Data Model

**Data source:** Direct Query or Import from `CustomerDW` SQL Server via `ls_sql_server` connection.

**Recommended tables to import into Power BI:**

| Table / View | Use in Power BI |
|---|---|
| `dbo.vw_CustomerSummary` | Main fact table for customer analysis |
| `dbo.vw_CustomersBySegment` | Pre-aggregated for Segment KPI cards |
| `dbo.vw_CustomersByCountry` | Pre-aggregated for geographic map visuals |
| `dbo.vw_MonthlySignups` | Line chart for acquisition trend |
| `dbo.vw_ETLRunSummary` | Pipeline health monitoring tile |

**Date table:** Create a calculated `DateTable` in Power BI using:

```dax
DateTable = CALENDAR(DATE(2000, 1, 1), TODAY())
```

Link `DateTable[Date]` → `vw_CustomerSummary[SignupDate]`.

---

### 8.2 KPIs and Measures

#### Total Customers

```dax
Total Customers = COUNTROWS('vw_CustomerSummary')
```

#### Premium Customers

```dax
Premium Customers = CALCULATE(
    COUNTROWS('vw_CustomerSummary'),
    'vw_CustomerSummary'[Segment] = "PREMIUM"
)
```

#### Premium Rate

```dax
Premium Rate = DIVIDE(
    CALCULATE(COUNTROWS('vw_CustomerSummary'), 'vw_CustomerSummary'[Segment] = "PREMIUM"),
    COUNTROWS('vw_CustomerSummary')
)
```

#### New Customers This Month

```dax
New Customers This Month = CALCULATE(
    COUNTROWS('vw_CustomerSummary'),
    MONTH('vw_CustomerSummary'[SignupDate]) = MONTH(TODAY()),
    YEAR('vw_CustomerSummary'[SignupDate]) = YEAR(TODAY())
)
```

#### Customers Without Email

```dax
Customers Without Email = CALCULATE(
    COUNTROWS('vw_CustomerSummary'),
    ISBLANK('vw_CustomerSummary'[Email])
)
```

#### Last Pipeline Run Status

```dax
Last Run Status = FIRSTNONBLANK('vw_ETLRunSummary'[Status], 1)
```

---

### 8.3 Dashboard Pages

#### Page 1 — Executive Overview

| Visual | Type | Fields |
|---|---|---|
| Total Customers | Card | `[Total Customers]` |
| Premium Rate | Gauge | `[Premium Rate]`, min 0, max 1 |
| New This Month | Card | `[New Customers This Month]` |
| Customers by Segment | Donut chart | `Segment`, `[Total Customers]` |
| Customers by Country | Filled map | `Country`, `[Total Customers]` |
| Pipeline Status | Card | `[Last Run Status]` |

#### Page 2 — Acquisition Trends

| Visual | Type | Fields |
|---|---|---|
| Monthly Signups | Line chart | `SignupYear`, `SignupMonth`, `[Total Customers]` |
| Signups by Segment | Clustered bar | `Segment`, `SignupYear`, `[Total Customers]` |
| Top 10 Countries | Horizontal bar | `Country`, `[Total Customers]` (top N = 10) |

#### Page 3 — Data Quality Monitoring

| Visual | Type | Fields |
|---|---|---|
| Source Distribution | Pie chart | `SourceSystem`, `[Total Customers]` |
| Customers Without Email | Card | `[Customers Without Email]` |
| Rows Loaded vs Rejected | Clustered bar | `RunStart`, `RowsLoaded`, `RowsRejected` |
| Pipeline Run History | Table | `PipelineName`, `RunStart`, `DurationSeconds`, `Status`, `RowsLoaded` |

---

*This document is the implementation-ready specification for the Customer Data ETL pipeline. All schemas, transformation rules, SQL scripts, and ADF artifacts described here are consistent with the files committed to this repository.*
