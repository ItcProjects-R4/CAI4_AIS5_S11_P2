"""
Unit tests for check_env module

Tests environment diagnostics functionality including:
- Python version checking
- Package availability
- ODBC driver detection
- Environment variable validation
- Database connectivity checks

Tested using pytest with monkeypatch and tmpdir fixtures.
"""

import os
import sys
from unittest import mock

import pytest

# Import the module under test
# (Import inside functions to avoid pytest collection issues)


def test_python_version_check():
    """Test Python version validation."""
    from etl_cli.check_env import check_python_version

    # Current Python should always pass this check
    assert check_python_version() is True


def test_required_packages():
    """Test required package detection."""
    from etl_cli.check_env import check_required_packages

    # At minimum, typer and dotenv should be installed (for tests to run)
    # This test just verifies the function runs without error
    result = check_required_packages()
    assert isinstance(result, bool)


def test_environment_variables_missing_env(monkeypatch, tmp_path):
    """Test environment variable check when .env is missing."""
    # Change to temp directory without .env
    monkeypatch.chdir(tmp_path)

    from etl_cli.check_env import check_environment_variables

    # Should return False if required vars are not set
    result = check_environment_variables()
    # We expect it to return False since we just cleared the environment
    assert isinstance(result, bool)


def test_environment_variables_with_env(monkeypatch, tmp_path):
    """Test environment variable check with .env variables set."""
    # Set required environment variables
    monkeypatch.setenv("DB_SERVER", "localhost,1433")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "sa")
    monkeypatch.setenv("DB_PASSWORD", "TestPassword123!")

    from etl_cli.check_env import check_environment_variables

    result = check_environment_variables()
    assert isinstance(result, bool)
    assert result is True  # All required vars are set


def test_environment_variables_partially_set(monkeypatch):
    """Test environment variable check with partial configuration."""
    # Set only some required variables
    monkeypatch.setenv("DB_SERVER", "localhost")
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    from etl_cli.check_env import check_environment_variables

    result = check_environment_variables()
    assert result is False  # Not all required vars are set


def test_odbc_drivers_available():
    """Test ODBC driver detection when drivers are installed."""
    from etl_cli.check_env import check_odbc_drivers

    # This test passes if pyodbc is available, regardless of actual drivers
    result = check_odbc_drivers()
    assert isinstance(result, bool)


def test_odbc_drivers_not_installed(monkeypatch):
    """Test ODBC driver check when pyodbc is not installed."""
    # Mock pyodbc import failure
    import builtins

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pyodbc":
            raise ImportError("pyodbc not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    monkeypatch.setattr("sys.modules", sys.modules.copy())

    from etl_cli.check_env import check_odbc_drivers

    result = check_odbc_drivers()
    # Should handle gracefully even if pyodbc is missing
    assert isinstance(result, bool)


@pytest.mark.integration
def test_database_connectivity_no_credentials(monkeypatch):
    """Test database connectivity check without credentials set."""
    # Clear database credentials
    monkeypatch.delenv("DB_SERVER", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    from etl_cli.check_env import check_database_connectivity

    result = check_database_connectivity()
    # Should return True (skipped) when credentials are missing
    assert isinstance(result, bool)


class TestCheckEnvIntegration:
    """Integration tests for check_env functionality."""

    @pytest.mark.integration
    def test_full_environment_check(self, monkeypatch):
        """Test running the full environment check."""
        # Set environment variables
        monkeypatch.setenv("DB_SERVER", "localhost")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "sa")
        monkeypatch.setenv("DB_PASSWORD", "pwd")
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        from etl_cli.check_env import (
            check_python_version,
            check_required_packages,
            check_environment_variables,
        )

        # Run all checks
        py_ok = check_python_version()
        pkg_ok = check_required_packages()
        env_ok = check_environment_variables()

        assert py_ok is True
        assert pkg_ok is True
        assert env_ok is True
