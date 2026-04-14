-- ============================================================
-- Script:  01_create_database.sql
-- Purpose: Create the CustomerDW database (run once on first setup)
-- Author:  ETL Team
-- Date:    2024-06-01
-- Version: 1.0
-- ============================================================
-- Run this script connected to the master database.
-- Safe to run again: uses IF NOT EXISTS guard.

USE master;
GO

IF NOT EXISTS (
    SELECT name
    FROM sys.databases
    WHERE name = N'CustomerDW'
)
BEGIN
    CREATE DATABASE CustomerDW
        COLLATE SQL_Latin1_General_CP1_CI_AS;
END;
GO

USE CustomerDW;
GO
