-- ============================================================
-- Script:  05_validation_queries.sql
-- Purpose: Data quality checks — run after every pipeline execution
-- Author:  ETL Team
-- Date:    2024-06-01
-- Version: 1.0
-- ============================================================
-- All queries return 0 rows / 0 count on a healthy load.
-- Any non-zero result requires investigation before sign-off.

USE CustomerDW;
GO

-- ----------------------------------------------------------
-- CHECK 1: Total row count (must be > 0)
-- ----------------------------------------------------------
SELECT COUNT(*) AS TotalCustomers
FROM dbo.Customers;
-- Expected: > 0

-- ----------------------------------------------------------
-- CHECK 2: Null CustomerID (must be 0)
-- ----------------------------------------------------------
SELECT COUNT(*) AS NullCustomerID
FROM dbo.Customers
WHERE CustomerID IS NULL;
-- Expected: 0

-- ----------------------------------------------------------
-- CHECK 3: Null or blank CustomerName (must be 0)
-- ----------------------------------------------------------
SELECT COUNT(*) AS BlankNames
FROM dbo.Customers
WHERE CustomerName IS NULL
   OR LTRIM(RTRIM(CustomerName)) = '';
-- Expected: 0

-- ----------------------------------------------------------
-- CHECK 4: Duplicate CustomerID (must return 0 rows)
-- ----------------------------------------------------------
SELECT CustomerID, COUNT(*) AS Occurrences
FROM dbo.Customers
GROUP BY CustomerID
HAVING COUNT(*) > 1;
-- Expected: 0 rows returned

-- ----------------------------------------------------------
-- CHECK 5: Invalid email format (must be 0 rows)
-- ----------------------------------------------------------
SELECT CustomerID, Email
FROM dbo.Customers
WHERE Email IS NOT NULL
  AND (
        Email NOT LIKE '%@%'
     OR Email NOT LIKE '%.%'
     OR Email <> LOWER(Email)   -- email must be lowercase
  );
-- Expected: 0 rows

-- ----------------------------------------------------------
-- CHECK 6: Unexpected Segment values (must show only allowed values)
-- ----------------------------------------------------------
SELECT DISTINCT Segment, COUNT(*) AS RecordCount
FROM dbo.Customers
GROUP BY Segment
ORDER BY RecordCount DESC;
-- Expected: only PREMIUM, STANDARD, BASIC, or NULL (documented exception)

SELECT COUNT(*) AS InvalidSegments
FROM dbo.Customers
WHERE Segment IS NOT NULL
  AND Segment NOT IN ('PREMIUM', 'STANDARD', 'BASIC');
-- Expected: 0

-- ----------------------------------------------------------
-- CHECK 7: SignupDate out of range (must be 0 rows)
-- ----------------------------------------------------------
SELECT CustomerID, SignupDate
FROM dbo.Customers
WHERE SignupDate IS NOT NULL
  AND (SignupDate < '2000-01-01' OR SignupDate > CAST(GETDATE() AS DATE));
-- Expected: 0 rows

-- ----------------------------------------------------------
-- CHECK 8: Source system distribution (both CRM and Excel expected)
-- ----------------------------------------------------------
SELECT SourceSystem, COUNT(*) AS RecordCount
FROM dbo.Customers
GROUP BY SourceSystem;
-- Expected: rows for both 'CRM' and 'Excel'

SELECT COUNT(*) AS MissingSourceSystem
FROM dbo.Customers
WHERE SourceSystem IS NULL;
-- Expected: 0

-- ----------------------------------------------------------
-- CHECK 9: Country values — must be full names, not ISO codes
-- ----------------------------------------------------------
SELECT CustomerID, Country
FROM dbo.Customers
WHERE Country IS NOT NULL
  AND LEN(Country) = 3
  AND Country = UPPER(Country);
-- Expected: 0 rows (ISO-3 codes must have been mapped to full names)

-- ----------------------------------------------------------
-- CHECK 10: Phone format check — must follow +XX-XXX-XXXXXXX pattern
-- ----------------------------------------------------------
SELECT CustomerID, Phone
FROM dbo.Customers
WHERE Phone IS NOT NULL
  AND Phone NOT LIKE '+[0-9][0-9]-[0-9][0-9][0-9]-%';
-- Expected: 0 rows for well-normalised records

-- ----------------------------------------------------------
-- CHECK 11: Row count by country (quick data profile)
-- ----------------------------------------------------------
SELECT Country, COUNT(*) AS CustomerCount
FROM dbo.Customers
GROUP BY Country
ORDER BY CustomerCount DESC;

-- ----------------------------------------------------------
-- CHECK 12: Latest pipeline run status
-- ----------------------------------------------------------
SELECT TOP 1
    PipelineName,
    RunStart,
    RunEnd,
    DATEDIFF(SECOND, RunStart, RunEnd)  AS DurationSeconds,
    RowsLoaded,
    RowsRejected,
    Status,
    Notes
FROM dbo.ETLRunLog
ORDER BY RunStart DESC;
-- Expected: Status = 'Success', RowsLoaded > 0

-- ----------------------------------------------------------
-- CHECK 13: Rejected records summary
-- ----------------------------------------------------------
SELECT RejectionReason, COUNT(*) AS RejectedCount
FROM dbo.RejectedRecords
GROUP BY RejectionReason
ORDER BY RejectedCount DESC;

-- ----------------------------------------------------------
-- CHECK 14: Customers with NULL SignupDate (documented exception)
-- ----------------------------------------------------------
SELECT COUNT(*) AS CustomersWithNullSignupDate
FROM dbo.Customers
WHERE SignupDate IS NULL;
-- Informational: NULL is allowed for records imported before 2022,
-- but the count should be compared with the known volume of pre-2022 imports.
