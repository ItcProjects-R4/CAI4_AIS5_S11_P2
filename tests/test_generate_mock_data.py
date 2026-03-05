"""
Unit tests for generate_mock_data module

Tests mock data generation functionality including:
- Data generation (CRM and Sales)
- File output (CSV and XLSX)
- Seeded reproducibility
- Row count validation
- Error handling

Uses pytest tmpdir fixture for isolated file operations.
"""

import tempfile
from pathlib import Path

import pytest


class TestGenerateCRMData:
    """Tests for CRM data generation."""

    def test_generate_crm_data_basic(self):
        """Test basic CRM data generation."""
        from etl_cli.generate_mock_data import generate_crm_data

        df = generate_crm_data(10, seed=42)

        assert len(df) == 10
        assert "customer_id" in df.columns
        assert "name" in df.columns
        assert "email" in df.columns
        assert "phone" in df.columns
        assert "country" in df.columns
        assert "registration_date" in df.columns

    def test_generate_crm_data_reproducibility(self):
        """Test that same seed produces same data."""
        from etl_cli.generate_mock_data import generate_crm_data

        df1 = generate_crm_data(20, seed=123)
        df2 = generate_crm_data(20, seed=123)

        # DataFrames should be identical
        assert df1.equals(df2)

    def test_generate_crm_data_different_seeds(self):
        """Test that different seeds produce different data."""
        from etl_cli.generate_mock_data import generate_crm_data

        df1 = generate_crm_data(20, seed=123)
        df2 = generate_crm_data(20, seed=456)

        # Names should be different (very likely)
        assert not df1["name"].equals(df2["name"])

    def test_generate_crm_data_row_count(self):
        """Test CRM data generation with various row counts."""
        from etl_cli.generate_mock_data import generate_crm_data

        for row_count in [1, 10, 100, 1000]:
            df = generate_crm_data(row_count, seed=42)
            assert len(df) == row_count

    def test_generate_crm_data_no_duplicates(self):
        """Test that customer_id is unique."""
        from etl_cli.generate_mock_data import generate_crm_data

        df = generate_crm_data(100, seed=42)

        assert df["customer_id"].is_unique

    def test_generate_crm_data_email_format(self):
        """Test that emails have valid format."""
        from etl_cli.generate_mock_data import generate_crm_data

        df = generate_crm_data(50, seed=42)

        for email in df["email"]:
            assert "@" in email
            assert "." in email


class TestGenerateSalesData:
    """Tests for Sales data generation."""

    def test_generate_sales_data_basic(self):
        """Test basic sales data generation."""
        from etl_cli.generate_mock_data import generate_sales_data

        df = generate_sales_data(10, seed=42, num_customers=5)

        assert len(df) == 10
        assert "transaction_id" in df.columns
        assert "customer_id" in df.columns
        assert "amount" in df.columns
        assert "date" in df.columns
        assert "product" in df.columns

    def test_generate_sales_data_reproducibility(self):
        """Test that same seed produces same sales data."""
        from etl_cli.generate_mock_data import generate_sales_data

        df1 = generate_sales_data(20, seed=789, num_customers=10)
        df2 = generate_sales_data(20, seed=789, num_customers=10)

        assert df1.equals(df2)

    def test_generate_sales_data_valid_customer_references(self):
        """Test that customer_id references are within valid range."""
        from etl_cli.generate_mock_data import generate_sales_data

        num_customers = 50
        df = generate_sales_data(100, seed=42, num_customers=num_customers)

        # All customer_ids should be <= num_customers
        assert df["customer_id"].max() <= num_customers
        assert df["customer_id"].min() >= 1

    def test_generate_sales_data_amounts_positive(self):
        """Test that transaction amounts are positive."""
        from etl_cli.generate_mock_data import generate_sales_data

        df = generate_sales_data(100, seed=42, num_customers=20)

        assert (df["amount"] > 0).all()
        assert df["amount"].min() >= 10
        assert df["amount"].max() <= 5000

    def test_generate_sales_data_unique_ids(self):
        """Test that transaction_id is unique."""
        from etl_cli.generate_mock_data import generate_sales_data

        df = generate_sales_data(100, seed=42, num_customers=20)

        assert df["transaction_id"].is_unique


class TestDataGeneration:
    """Integration tests for data file generation."""

    def test_generate_and_save_crm_csv(self, tmp_path):
        """Test generating and saving CRM data as CSV."""
        import pandas as pd

        from etl_cli.generate_mock_data import generate_crm_data

        df = generate_crm_data(25, seed=42)

        csv_path = tmp_path / "crm_data.csv"
        df.to_csv(csv_path, index=False)

        assert csv_path.exists()

        # Verify we can read it back
        df_read = pd.read_csv(csv_path)
        assert len(df_read) == 25
        assert list(df_read.columns) == list(df.columns)

    def test_generate_and_save_sales_xlsx(self, tmp_path):
        """Test generating and saving sales data as Excel."""
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            pytest.skip("openpyxl not installed")

        import pandas as pd

        from etl_cli.generate_mock_data import generate_sales_data

        df = generate_sales_data(25, seed=42, num_customers=10)

        xlsx_path = tmp_path / "sales_data.xlsx"
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        assert xlsx_path.exists()

        # Verify we can read it back
        df_read = pd.read_excel(xlsx_path, engine="openpyxl")
        assert len(df_read) == 25

    def test_generate_and_save_sales_csv_fallback(self, tmp_path):
        """Test generating and saving sales data as CSV (fallback for no Excel)."""
        import pandas as pd

        from etl_cli.generate_mock_data import generate_sales_data

        df = generate_sales_data(25, seed=42, num_customers=10)

        csv_path = tmp_path / "sales_data.csv"
        df.to_csv(csv_path, index=False)

        assert csv_path.exists()

        # Verify we can read it back
        df_read = pd.read_csv(csv_path)
        assert len(df_read) == 25

    def test_data_files_reproducible(self, tmp_path):
        """Test that running generation twice with same seed creates identical files."""
        import pandas as pd

        from etl_cli.generate_mock_data import generate_crm_data

        # Generate twice
        df1 = generate_crm_data(50, seed=999)
        df2 = generate_crm_data(50, seed=999)

        path1 = tmp_path / "data1.csv"
        path2 = tmp_path / "data2.csv"

        df1.to_csv(path1, index=False)
        df2.to_csv(path2, index=False)

        # Read back and compare
        df1_read = pd.read_csv(path1)
        df2_read = pd.read_csv(path2)

        assert df1_read.equals(df2_read)
