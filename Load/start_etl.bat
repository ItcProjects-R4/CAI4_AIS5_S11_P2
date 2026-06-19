@REM Windows batch script to start ETL with Docker PostgreSQL
@REM
@REM This script:
@REM  1. Starts Docker PostgreSQL container
@REM  2. Waits for PostgreSQL to be ready
@REM  3. Runs pre-flight health checks
@REM  4. Executes the ETL pipeline
@REM
@REM Usage:
@REM   start_etl.bat
@REM

@echo off
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║                    ETL STARTUP SCRIPT (Windows)                           ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker is not installed or not in PATH
    echo   Install Docker from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo ✓ Docker is installed

REM Start Docker PostgreSQL container
echo.
echo Starting Docker PostgreSQL container...
docker compose up -d

if errorlevel 1 (
    echo ✗ Failed to start Docker container
    echo   Run: docker compose up -d
    exit /b 1
)

echo ✓ Docker container started

REM Wait for PostgreSQL to be ready
echo.
echo Waiting for PostgreSQL to initialize (15 seconds)...
timeout /t 15 /nobreak

REM Run health checks
echo.
echo Running health checks...
python healthcheck.py

if errorlevel 1 (
    echo ✗ Health checks failed
    echo   Review diagnostics above and fix issues
    exit /b 1
)

REM Install dependencies if needed
echo.
echo Checking Python dependencies...
pip install -q -r etl_pipeline/requirements.txt

REM Run ETL
echo.
echo Starting ETL pipeline...
python -m etl_pipeline.main

if errorlevel 1 (
    echo ✗ ETL execution failed
    echo   Check logs in etl_pipeline/execution_logs/ directory
    exit /b 1
)

echo.
echo ✓ ETL completed successfully!
echo.
echo Reports and logs are available in:
echo   - etl_pipeline/execution_logs/       (execution logs and summaries)
echo   - reports/    (detailed reports)
echo   - etl_pipeline/architecture/   (flow diagrams)
echo.

pause
