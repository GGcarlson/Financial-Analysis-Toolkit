"""Tests for summary reporting functionality."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from capstone_finance.reporting.summary import (
    calculate_percentiles,
    calculate_success_rate,
    create_summary_report,
    create_summary_statistics,
    save_summary_csv,
)


class TestSummaryStatistics:
    """Test summary statistics calculation."""

    def create_toy_data(self) -> pd.DataFrame:
        """Create deterministic toy data for testing."""
        # Create simple test data with 2 paths, 3 years each
        data = [
            # Path 0 - successful (all positive balances)
            {
                "path": 0,
                "year": 2024,
                "age": 65,
                "balance": 1000000.0,
                "inflation": 0.02,
                "withdrawal_nominal": 40000.0,
            },
            {
                "path": 0,
                "year": 2025,
                "age": 66,
                "balance": 950000.0,
                "inflation": 0.025,
                "withdrawal_nominal": 41000.0,
            },
            {
                "path": 0,
                "year": 2026,
                "age": 67,
                "balance": 900000.0,
                "inflation": 0.03,
                "withdrawal_nominal": 42000.0,
            },
            # Path 1 - depleted (goes to 0)
            {
                "path": 1,
                "year": 2024,
                "age": 65,
                "balance": 1000000.0,
                "inflation": 0.02,
                "withdrawal_nominal": 40000.0,
            },
            {
                "path": 1,
                "year": 2025,
                "age": 66,
                "balance": 500000.0,
                "inflation": 0.025,
                "withdrawal_nominal": 41000.0,
            },
            {
                "path": 1,
                "year": 2026,
                "age": 67,
                "balance": 0.0,
                "inflation": 0.03,
                "withdrawal_nominal": 0.0,
            },
        ]
        return pd.DataFrame(data)

    def test_calculate_success_rate(self):
        """Test success rate calculation."""
        df = self.create_toy_data()

        # One path successful, one depleted = 50% success rate
        success_rate = calculate_success_rate(df)
        assert success_rate == 0.5

    def test_calculate_success_rate_all_successful(self):
        """Test success rate when all paths are successful."""
        df = self.create_toy_data()
        # Make all final balances positive
        df.loc[(df["year"] == 2026) & (df["path"] == 1), "balance"] = 100000.0

        success_rate = calculate_success_rate(df)
        assert success_rate == 1.0

    def test_calculate_success_rate_all_failed(self):
        """Test success rate when all paths fail."""
        df = self.create_toy_data()
        # Make all final balances zero
        df.loc[df["year"] == 2026, "balance"] = 0.0

        success_rate = calculate_success_rate(df)
        assert success_rate == 0.0

    def test_calculate_percentiles(self):
        """Test percentile calculation."""
        df = self.create_toy_data()

        percentiles = calculate_percentiles(df)

        # Check structure
        assert "yearly" in percentiles
        assert "final" in percentiles

        # Check yearly percentiles DataFrame
        yearly = percentiles["yearly"]
        assert len(yearly) == 3  # 3 years
        assert list(yearly.columns) == ["p10", "p50", "p90"]

        # Check final year percentiles
        final = percentiles["final"]
        assert "p10" in final
        assert "p50" in final
        assert "p90" in final

        # For year 2026, we have balances [900000, 0]
        # p10 should be close to 0, p50 should be 450000, p90 should be close to 900000
        assert final["p10"] == pytest.approx(90000.0, rel=0.1)
        assert final["p50"] == pytest.approx(450000.0, rel=0.1)
        assert final["p90"] == pytest.approx(810000.0, rel=0.1)

    def test_create_summary_statistics(self):
        """Test comprehensive summary statistics creation."""
        df = self.create_toy_data()

        stats = create_summary_statistics(df)

        # Check all expected keys
        expected_keys = [
            "success_rate",
            "percentiles",
            "yearly_stats",
            "final_year_stats",
            "depletion_by_year",
            "total_paths",
            "total_years",
        ]
        for key in expected_keys:
            assert key in stats

        # Verify values
        assert stats["success_rate"] == 0.5
        assert stats["total_paths"] == 2
        assert stats["total_years"] == 3

        # Check depletion by year
        assert stats["depletion_by_year"][2024] == 0
        assert stats["depletion_by_year"][2025] == 0
        assert stats["depletion_by_year"][2026] == 1

    def test_create_summary_report(self):
        """Test Rich table creation."""
        df = self.create_toy_data()
        params = {
            "init_balance": 1000000,
            "equity_pct": 0.6,
            "fees_bps": 50,
            "strategy": "test_strategy",
        }

        table = create_summary_report(df, "test_strategy", params)

        # Verify it's a Rich Table
        from rich.table import Table

        assert isinstance(table, Table)

        # Check table has title
        assert table.title == "Retirement Simulation Summary Report"

        # Check columns exist
        assert len(table.columns) == 3

    def test_save_summary_csv(self):
        """Test CSV export functionality."""
        df = self.create_toy_data()
        stats = create_summary_statistics(df)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Save summary CSV
            save_summary_csv(df, stats, tmp_path)

            # Verify file exists
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

            # Load and verify content
            summary_df = pd.read_csv(tmp_path)

            # Check columns
            expected_columns = ["metric_type", "metric_name", "value"]
            assert list(summary_df.columns) == expected_columns

            # Check some specific metrics exist
            metric_names = summary_df["metric_name"].tolist()
            assert "success_rate" in metric_names
            assert "total_paths" in metric_names
            assert "total_years" in metric_names

            # Verify success rate value
            success_rate_row = summary_df[summary_df["metric_name"] == "success_rate"]
            assert len(success_rate_row) == 1
            assert success_rate_row["value"].iloc[0] == 0.5

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(
            columns=[
                "path",
                "year",
                "age",
                "balance",
                "inflation",
                "withdrawal_nominal",
            ]
        )

        # Empty data should return NaN or handle gracefully
        # The function should handle empty data by returning NaN
        success_rate = calculate_success_rate(df)
        assert pd.isna(success_rate)

    def test_single_path_data(self):
        """Test with single path data."""
        data = [
            {
                "path": 0,
                "year": 2024,
                "age": 65,
                "balance": 1000000.0,
                "inflation": 0.02,
                "withdrawal_nominal": 40000.0,
            },
            {
                "path": 0,
                "year": 2025,
                "age": 66,
                "balance": 950000.0,
                "inflation": 0.025,
                "withdrawal_nominal": 41000.0,
            },
        ]
        df = pd.DataFrame(data)

        success_rate = calculate_success_rate(df)
        assert success_rate == 1.0  # Single successful path

        stats = create_summary_statistics(df)
        assert stats["total_paths"] == 1
        assert stats["total_years"] == 2
