#!/bin/bash
# Linux/Mac script to start ETL with Docker PostgreSQL
#
# This script:
#  1. Starts Docker PostgreSQL container
#  2. Waits for PostgreSQL to be ready
#  3. Runs pre-flight health checks
#  4. Executes the ETL pipeline
#
# Usage:
#   chmod +x start_etl.sh
#   ./start_etl.sh

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║                   ETL STARTUP SCRIPT (Linux/Mac)                          ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed or not in PATH"
    echo "  Install Docker from: https://www.docker.com/"
    exit 1
fi

echo "✓ Docker is installed"

# Start Docker PostgreSQL container
echo ""
echo "Starting Docker PostgreSQL container..."
docker compose up -d

echo "✓ Docker container started"

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to initialize (15 seconds)..."
sleep 15

# Run health checks
echo ""
echo "Running health checks..."
python3 healthcheck.py || {
    echo "✗ Health checks failed"
    echo "  Review diagnostics above and fix issues"
    exit 1
}

# Install dependencies if needed
echo ""
echo "Checking Python dependencies..."
pip3 install -q -r etl_pipeline/requirements.txt

# Run ETL
echo ""
echo "Starting ETL pipeline..."
python3 -m etl_pipeline.main || {
    echo "✗ ETL execution failed"
    echo "  Check logs in etl_pipeline/execution_logs/ directory"
    exit 1
}

echo ""
echo "✓ ETL completed successfully!"
echo ""
echo "Reports and logs are available in:"
echo "  - etl_pipeline/execution_logs/       (execution logs and summaries)"
echo "  - reports/    (detailed reports)"
echo "  - etl_pipeline/architecture/   (flow diagrams)"
echo ""

