.PHONY: help build up shell down test lint fmt clean clean-docker

# Default target
help:
	@echo "Customer Data ETL - Makefile Targets"
	@echo "======================================="
	@echo ""
	@echo "Build and Run:"
	@echo "  make build          Build the Docker image"
	@echo "  make up             Start the container in background"
	@echo "  make shell          Open interactive shell in container"
	@echo "  make down           Stop and remove containers"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run pytest inside container"
	@echo "  make lint           Run flake8 checks"
	@echo "  make fmt            Format code with black and isort"
	@echo "  make fmt-check      Check formatting without changes"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove generated data artifacts"
	@echo "  make clean-docker   Remove Docker containers and volumes"
	@echo ""
	@echo "For full details, see README.md"

# Build Docker image
build:
	docker compose build

# Start container in background
up:
	docker compose up -d
	@echo "Container started. Run 'make shell' to enter, or 'make down' to stop."

# Open interactive shell
shell:
	docker compose run --rm etl bash

# Stop and remove containers
down:
	docker compose down

# Run tests
test:
	docker compose run --rm etl pytest

# Run linting (flake8)
lint:
	docker compose run --rm etl flake8 src tests

# Format code (black and isort)
fmt:
	docker compose run --rm etl bash -c "black src tests && isort src tests"

# Check formatting
fmt-check:
	docker compose run --rm etl bash -c "black --check src tests && isort --check-only src tests"

# Run check-env diagnostic
check-env:
	docker compose run --rm etl python -m etl_cli check_env

# Generate mock data
mock-data:
	docker compose run --rm etl python -m etl_cli generate_mock_data --rows 50 --seed 42

# Remove generated data
clean:
	docker compose run --rm etl python -m etl_cli clean
	@echo "Generated data cleaned."

# Remove Docker containers and volumes
clean-docker:
	docker compose down -v
	@echo "Containers and volumes removed."

# Install pre-commit hooks locally (optional, for host machine)
install-hooks:
	pre-commit install
	@echo "Pre-commit hooks installed."

# Run pre-commit on all files (optional)
pre-commit:
	pre-commit run --all-files
