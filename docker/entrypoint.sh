#!/bin/bash
# Customer Data ETL Docker Entrypoint
# Minimal wrapper to run commands inside the container
# Usage: docker compose run --rm etl <command>
#        docker compose run --rm etl bash
#        docker compose run --rm etl python -m etl_cli check_env

set -e

if [ "$#" -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'EOF'

Customer Data ETL - Docker Entrypoint
======================================

Usage:
  docker compose run --rm etl bash
    Opens an interactive shell inside the container

  docker compose run --rm etl python -m etl_cli check_env
    Runs environment diagnostics

  docker compose run --rm etl python -m etl_cli generate_mock_data --rows 50 --seed 42
    Generates mock customer data

  docker compose run --rm etl pytest
    Runs unit tests

  docker compose run --rm etl flake8 src tests
    Runs linting checks

  docker compose run --rm etl <any command>
    Runs the specified command inside the container

For more info, see README.md or run:
  docker compose run --rm etl python -m etl_cli --help

EOF
    exit 0
fi

exec "$@"
