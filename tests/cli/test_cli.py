"""Tests for CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from typer.testing import CliRunner

from capstone_finance.cli import app, create_results_dataframe, get_available_strategies
from capstone_finance.core.models import YearState


class TestCLI:
    """Tests for CLI application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_list_strategies_command(self):
        """Test the list-strategies command."""
        result = self.runner.invoke(app, ["list-strategies"])
        assert result.exit_code == 0
        assert "Available withdrawal strategies" in result.stdout
        assert "four_percent_rule" in result.stdout

    def test_version_command(self):
        """Test the version command."""
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Financial Analysis Toolkit" in result.stdout

    def test_retire_command_basic(self):
        """Test basic retire command execution."""
        result = self.runner.invoke(app, [
            "retire",
            "--strategy", "four_percent_rule",
            "--years", "5",
            "--paths", "10",
            "--seed", "42"
        ])
        assert result.exit_code == 0
        assert "Simulation completed successfully" in result.stdout
        assert "Strategy: four_percent_rule" in result.stdout
        assert "Years: 5" in result.stdout
        assert "Paths: 10" in result.stdout

    def test_retire_command_with_csv_output(self):
        """Test retire command with CSV output."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            result = self.runner.invoke(app, [
                "retire",
                "--strategy", "four_percent_rule",
                "--years", "3",
                "--paths", "5",
                "--seed", "42",
                "--output", tmp_path
            ])
            
            assert result.exit_code == 0
            assert "Simulation completed successfully" in result.stdout
            assert f"Results saved to: {tmp_path}" in result.stdout
            
            # Verify CSV file was created and has expected structure
            assert Path(tmp_path).exists()
            df = pd.read_csv(tmp_path)
            
            # Check expected columns
            expected_columns = ["path", "year", "age", "balance", "inflation", "withdrawal_nominal"]
            assert all(col in df.columns for col in expected_columns)
            
            # Check we have the expected number of rows (paths * years)
            assert len(df) == 5 * 3  # 5 paths * 3 years
            
            # Check paths are numbered correctly
            assert set(df['path'].unique()) == {0, 1, 2, 3, 4}
            
        finally:
            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

    def test_retire_command_invalid_strategy(self):
        """Test retire command with invalid strategy."""
        result = self.runner.invoke(app, [
            "retire",
            "--strategy", "nonexistent_strategy",
            "--years", "5",
            "--paths", "10"
        ])
        assert result.exit_code == 1
        assert "Strategy 'nonexistent_strategy' not found" in result.stdout

    def test_retire_command_invalid_equity_pct(self):
        """Test retire command with invalid equity percentage."""
        result = self.runner.invoke(app, [
            "retire",
            "--equity-pct", "1.5",  # Invalid: > 1.0
            "--years", "5",
            "--paths", "10"
        ])
        assert result.exit_code == 1
        assert "Equity percentage must be between 0 and 1" in result.stdout

    def test_retire_command_invalid_years(self):
        """Test retire command with invalid years."""
        result = self.runner.invoke(app, [
            "retire",
            "--years", "0",  # Invalid: <= 0
            "--paths", "10"
        ])
        assert result.exit_code == 1
        assert "Years must be positive" in result.stdout

    def test_retire_command_invalid_paths(self):
        """Test retire command with invalid paths."""
        result = self.runner.invoke(app, [
            "retire",
            "--years", "5",
            "--paths", "-1"  # Invalid: <= 0
        ])
        assert result.exit_code == 1
        assert "Paths must be positive" in result.stdout

    def test_retire_command_invalid_market_mode(self):
        """Test retire command with invalid market mode."""
        result = self.runner.invoke(app, [
            "retire",
            "--market-mode", "invalid_mode",
            "--years", "5",
            "--paths", "10"
        ])
        assert result.exit_code == 1
        assert "Market mode must be 'lognormal' or 'bootstrap'" in result.stdout

    def test_retire_command_with_all_options(self):
        """Test retire command with all options specified."""
        result = self.runner.invoke(app, [
            "retire",
            "--strategy", "four_percent_rule",
            "--years", "5",
            "--paths", "10",
            "--seed", "123",
            "--init-balance", "500000",
            "--equity-pct", "0.8",
            "--fees-bps", "75",
            "--market-mode", "lognormal",
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Simulation completed successfully" in result.stdout
        assert "Initial Balance: $500,000.00" in result.stdout
        assert "Equity Allocation: 80.0%" in result.stdout
        assert "Annual Fees: 75 bps" in result.stdout

    def test_retire_command_bootstrap_mode(self):
        """Test retire command with bootstrap market mode."""
        result = self.runner.invoke(app, [
            "retire",
            "--strategy", "four_percent_rule",
            "--years", "3",
            "--paths", "5",
            "--market-mode", "bootstrap",
            "--seed", "42"
        ])
        assert result.exit_code == 0
        assert "Simulation completed successfully" in result.stdout
        assert "Market Mode: bootstrap" in result.stdout


class TestCLIUtilityFunctions:
    """Tests for CLI utility functions."""

    def test_get_available_strategies(self):
        """Test strategy discovery function."""
        strategies = get_available_strategies()
        assert isinstance(strategies, dict)
        assert "four_percent_rule" in strategies
        assert "dummy" in strategies

    def test_create_results_dataframe(self):
        """Test conversion of simulation results to DataFrame."""
        # Create mock simulation results
        results = [
            [  # Path 0
                YearState(year=2024, age=65, balance=1000000.0, inflation=0.02, withdrawal_nominal=40000.0),
                YearState(year=2025, age=66, balance=980000.0, inflation=0.03, withdrawal_nominal=41200.0),
            ],
            [  # Path 1
                YearState(year=2024, age=65, balance=1000000.0, inflation=0.02, withdrawal_nominal=40000.0),
                YearState(year=2025, age=66, balance=970000.0, inflation=0.025, withdrawal_nominal=41000.0),
            ]
        ]
        
        df = create_results_dataframe(results)
        
        # Check structure
        expected_columns = ["path", "year", "age", "balance", "inflation", "withdrawal_nominal"]
        assert all(col in df.columns for col in expected_columns)
        
        # Check data
        assert len(df) == 4  # 2 paths * 2 years each
        assert set(df['path'].unique()) == {0, 1}
        assert set(df['year'].unique()) == {2024, 2025}
        assert df['balance'].min() == 970000.0
        assert df['balance'].max() == 1000000.0

    @patch('capstone_finance.cli.importlib.metadata.entry_points')
    def test_get_available_strategies_with_error(self, mock_entry_points):
        """Test strategy discovery with loading errors."""
        from unittest.mock import MagicMock
        
        # Mock entry point that raises exception when loaded
        mock_ep = MagicMock()
        mock_ep.name = "broken_strategy"
        mock_ep.load.side_effect = ImportError("Module not found")
        
        mock_entry_points.return_value = [mock_ep]
        
        strategies = get_available_strategies()
        assert isinstance(strategies, dict)
        # Should handle the error gracefully and not include the broken strategy
        assert "broken_strategy" not in strategies

    def test_help_command(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Financial Analysis Toolkit" in result.stdout
        assert "retire" in result.stdout
        assert "list-strategies" in result.stdout
        assert "version" in result.stdout

    def test_retire_help_command(self):
        """Test retire command help output."""
        runner = CliRunner()
        result = runner.invoke(app, ["retire", "--help"])
        assert result.exit_code == 0
        assert "--strategy" in result.stdout
        assert "--years" in result.stdout
        assert "--paths" in result.stdout
        assert "--output" in result.stdout