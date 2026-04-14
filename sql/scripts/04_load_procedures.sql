-- ============================================================
-- Script:  04_load_procedures.sql
-- Purpose: Stored procedures for staging-to-target upsert
--          and ETL run logging
-- Author:  ETL Team
-- Date:    2024-06-01
-- Version: 1.0
-- ============================================================
-- Uses CREATE OR ALTER so it is safe to run more than once.

USE CustomerDW;
GO

-- ----------------------------------------------------------
-- Procedure: dbo.usp_UpsertCustomers
-- Merges rows from CustomerStaging into Customers, then
-- clears the staging table.
--
-- Called by ADF Stored Procedure Activity after the Data Flow
-- has finished loading dbo.CustomerStaging.
-- ----------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.usp_UpsertCustomers AS
BEGIN
    SET NOCOUNT ON;

    MERGE dbo.Customers AS target
    USING (
        -- Deduplicate staging before merge: keep one row per CustomerID
        -- ordered by SourceSystem (CRM preferred) then LoadedAt descending.
        SELECT
            CustomerID,
            CustomerName,
            Email,
            Phone,
            SignupDate,
            Country,
            Segment,
            SourceSystem,
            LoadedAt
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY CustomerID
                    ORDER BY
                        CASE WHEN SourceSystem = 'CRM' THEN 0 ELSE 1 END,
                        LoadedAt DESC
                ) AS rn
            FROM dbo.CustomerStaging
            WHERE CustomerID IS NOT NULL
        ) ranked
        WHERE rn = 1
    ) AS source
        ON target.CustomerID = source.CustomerID
    WHEN MATCHED THEN
        UPDATE SET
            CustomerName  = source.CustomerName,
            Email         = source.Email,
            Phone         = source.Phone,
            SignupDate    = source.SignupDate,
            Country       = source.Country,
            Segment       = source.Segment,
            SourceSystem  = source.SourceSystem,
            LoadedAt      = GETUTCDATE()
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (CustomerID, CustomerName, Email, Phone,
                SignupDate, Country, Segment, SourceSystem, LoadedAt)
        VALUES (source.CustomerID, source.CustomerName, source.Email, source.Phone,
                source.SignupDate, source.Country, source.Segment,
                source.SourceSystem, GETUTCDATE());

    TRUNCATE TABLE dbo.CustomerStaging;
END;
GO

-- ----------------------------------------------------------
-- Procedure: dbo.usp_LogETLRun
-- Records the start or end of a pipeline run in ETLRunLog.
--
-- Parameters:
--   @PipelineName   NVARCHAR(100) — name of the ADF pipeline
--   @Action         NVARCHAR(10)  — 'START' or 'END'
--   @RunID          INT OUTPUT    — run ID (returned on START, passed on END)
--   @RowsLoaded     INT           — rows successfully loaded (END only)
--   @RowsRejected   INT           — rows rejected (END only)
--   @Status         NVARCHAR(20)  — 'Success' or 'Failed' (END only)
--   @Notes          NVARCHAR(MAX) — optional notes
-- ----------------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.usp_LogETLRun
    @PipelineName   NVARCHAR(100),
    @Action         NVARCHAR(10),
    @RunID          INT             = NULL OUTPUT,
    @RowsLoaded     INT             = NULL,
    @RowsRejected   INT             = NULL,
    @Status         NVARCHAR(20)    = NULL,
    @Notes          NVARCHAR(MAX)   = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @Action = 'START'
    BEGIN
        INSERT INTO dbo.ETLRunLog (PipelineName, RunStart, Status)
        VALUES (@PipelineName, GETUTCDATE(), 'Running');

        SET @RunID = SCOPE_IDENTITY();
    END
    ELSE IF @Action = 'END'
    BEGIN
        UPDATE dbo.ETLRunLog
        SET
            RunEnd        = GETUTCDATE(),
            RowsLoaded    = @RowsLoaded,
            RowsRejected  = @RowsRejected,
            Status        = @Status,
            Notes         = @Notes
        WHERE RunID = @RunID;
    END;
END;
GO
