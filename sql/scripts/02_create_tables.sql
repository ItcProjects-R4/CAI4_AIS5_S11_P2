-- ============================================================
-- Script:  02_create_tables.sql
-- Purpose: Create all target tables for the CustomerDW database
-- Author:  ETL Team
-- Date:    2024-06-01
-- Version: 1.0
-- ============================================================
-- Idempotent: uses IF NOT EXISTS so it is safe to run more than once.

USE CustomerDW;
GO

-- ----------------------------------------------------------
-- Table: dbo.Customers
-- The main table holding all final, clean customer records.
-- ----------------------------------------------------------
IF NOT EXISTS (
    SELECT 1
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'dbo' AND t.name = 'Customers'
)
BEGIN
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
END;
GO

-- ----------------------------------------------------------
-- Table: dbo.CustomerStaging
-- Temporary buffer table used by the ADF pipeline.
-- No primary key — allows NULLs so bulk-load does not fail.
-- ----------------------------------------------------------
IF NOT EXISTS (
    SELECT 1
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'dbo' AND t.name = 'CustomerStaging'
)
BEGIN
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
END;
GO

-- ----------------------------------------------------------
-- Table: dbo.RejectedRecords
-- Stores rows that failed validation during pipeline execution.
-- ----------------------------------------------------------
IF NOT EXISTS (
    SELECT 1
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'dbo' AND t.name = 'RejectedRecords'
)
BEGIN
    CREATE TABLE dbo.RejectedRecords (
        RejectionID     INT             NOT NULL IDENTITY(1,1),
        SourceSystem    NVARCHAR(20)        NULL,
        RawCustomerID   NVARCHAR(50)        NULL,
        RawName         NVARCHAR(500)       NULL,
        RawEmail        NVARCHAR(500)       NULL,
        RawPhone        NVARCHAR(100)       NULL,
        RawSignupDate   NVARCHAR(100)       NULL,
        RawCountry      NVARCHAR(200)       NULL,
        RawSegment      NVARCHAR(100)       NULL,
        RejectionReason NVARCHAR(500)   NOT NULL,
        RejectedAt      DATETIME2(0)    NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_RejectedRecords PRIMARY KEY (RejectionID)
    );
END;
GO

-- ----------------------------------------------------------
-- Table: dbo.ETLRunLog
-- Audit log recording the outcome of every pipeline run.
-- ----------------------------------------------------------
IF NOT EXISTS (
    SELECT 1
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'dbo' AND t.name = 'ETLRunLog'
)
BEGIN
    CREATE TABLE dbo.ETLRunLog (
        RunID           INT             NOT NULL IDENTITY(1,1),
        PipelineName    NVARCHAR(100)   NOT NULL,
        RunStart        DATETIME2(0)    NOT NULL,
        RunEnd          DATETIME2(0)        NULL,
        RowsLoaded      INT                 NULL,
        RowsRejected    INT                 NULL,
        Status          NVARCHAR(20)        NULL,  -- 'Running' | 'Success' | 'Failed'
        Notes           NVARCHAR(MAX)       NULL,

        CONSTRAINT PK_ETLRunLog PRIMARY KEY (RunID)
    );
END;
GO
