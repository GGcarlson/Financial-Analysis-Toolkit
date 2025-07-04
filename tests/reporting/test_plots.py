"""Tests for plotting functionality."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from capstone_finance.reporting.plots import (
    create_equity_curve_plot,
    create_success_rate_by_year_plot,
    create_withdrawal_plot,
)


class TestPlots:
    """Test plotting functions."""

    def create_test_data(self) -> pd.DataFrame:
        """Create test data for plotting."""
        # Create data with 3 paths, 5 years each
        data = []
        for path in range(3):
            for year_offset in range(5):
                year = 2024 + year_offset
                age = 65 + year_offset
                # Create some variation in balances
                if path == 0:
                    # Path 0: steady decline
                    balance = 1000000 - (year_offset * 100000)
                elif path == 1:
                    # Path 1: volatile but surviving
                    balance = 1000000 + (
                        year_offset * 50000 if year_offset % 2 == 0 else -50000
                    )
                else:
                    # Path 2: depletes in year 4
                    balance = max(0, 1000000 - (year_offset * 250000))

                withdrawal = 40000 + (year_offset * 1000) if balance > 0 else 0

                data.append(
                    {
                        "path": path,
                        "year": year,
                        "age": age,
                        "balance": balance,
                        "inflation": 0.02 + (year_offset * 0.005),
                        "withdrawal_nominal": withdrawal,
                    }
                )

        return pd.DataFrame(data)

    def test_create_equity_curve_plot(self):
        """Test equity curve plot creation."""
        df = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Create plot
            create_equity_curve_plot(df, tmp_path)

            # Verify file exists and has content
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_create_equity_curve_plot_with_params(self):
        """Test equity curve plot with parameters."""
        df = self.create_test_data()
        params = {
            "init_balance": 1000000,
            "equity_pct": 0.7,
            "strategy": "test_strategy",
        }

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Create plot with custom title and parameters
            create_equity_curve_plot(
                df, tmp_path, title="Test Portfolio Balance", params=params
            )

            # Verify file exists and has content
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_create_withdrawal_plot(self):
        """Test withdrawal plot creation."""
        df = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Create plot
            create_withdrawal_plot(df, tmp_path)

            # Verify file exists and has content
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_create_success_rate_plot(self):
        """Test success rate plot creation."""
        df = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Create plot
            create_success_rate_by_year_plot(df, tmp_path)

            # Verify file exists and has content
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_plot_with_custom_title(self):
        """Test plots with custom titles."""
        df = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Create plot with custom title
            create_withdrawal_plot(df, tmp_path, title="Custom Withdrawal Analysis")

            # Verify file exists
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

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

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Should handle empty data gracefully (might create empty plot or raise)
            with pytest.raises(Exception):
                create_equity_curve_plot(df, tmp_path)

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_single_path_plot(self):
        """Test plotting with single path data."""
        # Create single path data
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
            {
                "path": 0,
                "year": 2026,
                "age": 67,
                "balance": 900000.0,
                "inflation": 0.03,
                "withdrawal_nominal": 42000.0,
            },
        ]
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Should work with single path
            create_equity_curve_plot(df, tmp_path)

            # Verify file exists and has content
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_plot_output_formats(self):
        """Test different output path formats."""
        df = self.create_test_data()

        # Test with Path object
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            create_equity_curve_plot(df, tmp_path)
            assert tmp_path.exists()
        finally:
            tmp_path.unlink(missing_ok=True)

        # Test with string path
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path_str = tmp_file.name

        try:
            create_equity_curve_plot(df, tmp_path_str)
            assert Path(tmp_path_str).exists()
        finally:
            Path(tmp_path_str).unlink(missing_ok=True)

    def test_matplotlib_backend(self):
        """Test that matplotlib is using non-interactive backend."""
        import matplotlib

        # Should be using Agg backend for headless operation
        assert matplotlib.get_backend() == "Agg"
