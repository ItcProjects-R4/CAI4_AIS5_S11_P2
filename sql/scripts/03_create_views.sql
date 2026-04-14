-- ============================================================
-- Script:  03_create_views.sql
-- Purpose: Create reporting views over the CustomerDW tables
-- Author:  ETL Team
-- Date:    2024-06-01
-- Version: 1.0
-- ============================================================
-- Uses CREATE OR ALTER so it is safe to run more than once.

USE CustomerDW;
GO

-- ----------------------------------------------------------
-- View: dbo.vw_CustomerSummary
-- Simplified reporting view with derived time columns for
-- easy year/month-based slicing in Power BI or SQL queries.
-- ----------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_CustomerSummary AS
SELECT
    CustomerID,
    CustomerName,
    Email,
    Phone,
    Country,
    Segment,
    SignupDate,
    YEAR(SignupDate)    AS SignupYear,
    MONTH(SignupDate)   AS SignupMonth,
    SourceSystem,
    LoadedAt
FROM dbo.Customers;
GO

-- ----------------------------------------------------------
-- View: dbo.vw_CustomersBySegment
-- Aggregate count per segment for dashboard KPI tiles.
-- ----------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_CustomersBySegment AS
SELECT
    Segment,
    COUNT(*)            AS CustomerCount
FROM dbo.Customers
GROUP BY Segment;
GO

-- ----------------------------------------------------------
-- View: dbo.vw_CustomersByCountry
-- Aggregate count per country for geographic analysis.
-- ----------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_CustomersByCountry AS
SELECT
    Country,
    COUNT(*)            AS CustomerCount
FROM dbo.Customers
GROUP BY Country;
GO

-- ----------------------------------------------------------
-- View: dbo.vw_MonthlySignups
-- Monthly customer acquisition trend.
-- ----------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_MonthlySignups AS
SELECT
    YEAR(SignupDate)    AS SignupYear,
    MONTH(SignupDate)   AS SignupMonth,
    COUNT(*)            AS NewCustomers
FROM dbo.Customers
WHERE SignupDate IS NOT NULL
GROUP BY YEAR(SignupDate), MONTH(SignupDate);
GO

-- ----------------------------------------------------------
-- View: dbo.vw_ETLRunSummary
-- Latest pipeline run details for monitoring dashboards.
-- ----------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_ETLRunSummary AS
SELECT TOP (1)
    RunID,
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
GO
