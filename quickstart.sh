#!/usr/bin/env bash
# Quick Start Script for Customer Data ETL
#
# This script automates the initial setup. Run it once after cloning/scaffolding.
# Usage: bash quickstart.sh
#
# What it does:
# 1. Checks for Docker
# 2. Copies .env.template to .env (skips if already exists)
# 3. Builds the Docker image
# 4. Verifies environment
# 5. Generates mock data
# 6. Runs tests
# 7. Shows next steps

set -e

echo "🚀 Customer Data ETL - Quick Start"
echo "=================================="
echo ""

# Check Docker
echo "📦 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✓ Docker found: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Install from: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "✓ Docker Compose found: $(docker compose version)"
echo ""

# Setup .env
echo "🔧 Setting up environment..."
if [ -f ".env" ]; then
    echo "✓ .env already exists (skipping)"
else
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✓ Created .env from template"
        echo "  ⚠️  Edit .env if you have real database credentials"
    else
        echo "❌ .env.template not found"
        exit 1
    fi
fi
echo ""

# Build Docker image
echo "🏗️  Building Docker image..."
echo "   (This may take 2-3 minutes on first build)"
if docker compose build; then
    echo "✓ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi
echo ""

# Check environment
echo "🔍 Checking environment..."
if docker compose run --rm etl python -m etl_cli check_env; then
    echo "✓ Environment checks passed"
else
    echo "⚠️  Some environment checks failed (may be expected)"
fi
echo ""

# Generate mock data
echo "🌱 Generating mock data..."
if docker compose run --rm etl python -m etl_cli generate_mock_data --rows 50 --seed 42; then
    echo "✓ Mock data generated"
else
    echo "⚠️  Mock data generation had issues"
fi
echo ""

# Run tests
echo "✅ Running tests..."
if docker compose run --rm etl pytest --tb=short; then
    echo "✓ All tests passed!"
else
    echo "❌ Some tests failed"
    exit 1
fi
echo ""

# Show next steps
echo "🎉 Quick start complete!"
echo ""
echo "Next steps:"
echo "  1. Open interactive shell:"
echo "     docker compose run --rm etl bash"
echo "     (or: make shell)"
echo ""
echo "  2. Run the ETL pipeline:"
echo "     docker compose run --rm etl python -m etl_cli run_pipeline"
echo ""
echo "  3. Make code changes in src/etl_cli/ and re-run tests:"
echo "     docker compose run --rm etl pytest"
echo ""
echo "  4. Check code quality:"
echo "     docker compose run --rm etl flake8 src tests"
echo ""
echo "For more detailed setup info, see SETUP_GUIDE.md"
echo ""
