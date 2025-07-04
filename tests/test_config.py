"""Tests for configuration functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from capstone_finance.config import ConfigModel


class TestConfigModel:
    """Tests for ConfigModel class."""

    def test_default_initialization(self):
        """Test ConfigModel with default values."""
        config = ConfigModel()

        # Test core defaults
        assert config.strategy == "four_percent_rule"
        assert config.years == 30
        assert config.paths == 1000
        assert config.seed == 42

        # Test portfolio defaults
        assert config.init_balance == 1_000_000.0
        assert config.equity_pct == 0.6
        assert config.fees_bps == 50

        # Test strategy-specific defaults
        assert config.percent == 0.05
        assert config.alpha == 0.7
        assert config.beta == 0.3
        assert config.window == 3

        # Test Guyton-Klinger defaults
        assert config.initial_rate == 0.05
        assert config.guard_pct == 0.20
        assert config.raise_pct == 0.10
        assert config.cut_pct == 0.10

    def test_custom_initialization(self):
        """Test ConfigModel with custom values."""
        config = ConfigModel(
            strategy="guyton_klinger",
            years=40,
            paths=5000,
            init_balance=2_000_000.0,
            initial_rate=0.045,
            guard_pct=0.25,
        )

        assert config.strategy == "guyton_klinger"
        assert config.years == 40
        assert config.paths == 5000
        assert config.init_balance == 2_000_000.0
        assert config.initial_rate == 0.045
        assert config.guard_pct == 0.25

        # Other values should be defaults
        assert config.equity_pct == 0.6
        assert config.raise_pct == 0.10

    def test_validation_errors(self):
        """Test that validation errors are properly raised."""
        # Test invalid equity_pct
        with pytest.raises(ValueError):
            ConfigModel(equity_pct=1.5)

        # Test invalid years
        with pytest.raises(ValueError):
            ConfigModel(years=0)

        # Test invalid market_mode
        with pytest.raises(ValueError):
            ConfigModel(market_mode="invalid")

        # Test invalid alpha + beta
        with pytest.raises(ValueError):
            ConfigModel(alpha=0.6, beta=0.5)  # Sum = 1.1

    def test_from_yaml_basic(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "strategy": "endowment",
            "years": 25,
            "paths": 2000,
            "init_balance": 1500000.0,
            "alpha": 0.8,
            "beta": 0.2,
            "verbose": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = ConfigModel.from_yaml(config_path)

            assert config.strategy == "endowment"
            assert config.years == 25
            assert config.paths == 2000
            assert config.init_balance == 1500000.0
            assert config.alpha == 0.8
            assert config.beta == 0.2
            assert config.verbose is True

            # Check defaults for unspecified values
            assert config.equity_pct == 0.6
            assert config.fees_bps == 50

        finally:
            Path(config_path).unlink()

    def test_from_yaml_empty_file(self):
        """Test loading from empty YAML file uses defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")  # Empty file
            config_path = f.name

        try:
            config = ConfigModel.from_yaml(config_path)

            # Should use all defaults
            assert config.strategy == "four_percent_rule"
            assert config.years == 30
            assert config.init_balance == 1_000_000.0

        finally:
            Path(config_path).unlink()

    def test_from_yaml_file_not_found(self):
        """Test error handling for missing config file."""
        with pytest.raises(FileNotFoundError):
            ConfigModel.from_yaml("nonexistent_config.yml")

    def test_from_yaml_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name

        try:
            with pytest.raises(yaml.YAMLError):
                ConfigModel.from_yaml(config_path)
        finally:
            Path(config_path).unlink()

    def test_to_yaml(self):
        """Test saving configuration to YAML file."""
        config = ConfigModel(
            strategy="guyton_klinger",
            years=35,
            init_balance=1500000.0,
            initial_rate=0.045,
            verbose=True,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            config_path = f.name

        try:
            config.to_yaml(config_path)

            # Load back and verify
            loaded_config = ConfigModel.from_yaml(config_path)
            assert loaded_config.strategy == "guyton_klinger"
            assert loaded_config.years == 35
            assert loaded_config.init_balance == 1500000.0
            assert loaded_config.initial_rate == 0.045
            assert loaded_config.verbose is True

        finally:
            Path(config_path).unlink()

    def test_merge_cli_args(self):
        """Test merging CLI arguments with config."""
        # Start with config file values
        config = ConfigModel(
            strategy="four_percent_rule",
            years=30,
            paths=1000,
            init_balance=1_000_000.0,
            verbose=False,
        )

        # Merge with CLI args (some None, some values)
        merged = config.merge_cli_args(
            strategy="guyton_klinger",  # Override
            years=None,  # Don't override
            paths=2000,  # Override
            init_balance=None,  # Don't override
            verbose=True,  # Override
            initial_rate=0.045,  # Override Guyton-Klinger parameter
        )

        # Check that CLI args took precedence
        assert merged.strategy == "guyton_klinger"  # Overridden
        assert merged.years == 30  # Kept original
        assert merged.paths == 2000  # Overridden
        assert merged.init_balance == 1_000_000.0  # Kept original
        assert merged.verbose is True  # Overridden
        assert merged.initial_rate == 0.045  # Overridden

        # Original config should be unchanged
        assert config.strategy == "four_percent_rule"
        assert config.paths == 1000
        assert config.verbose is False

    def test_merge_cli_args_ignores_invalid_keys(self):
        """Test that merge_cli_args ignores invalid keys."""
        config = ConfigModel()

        # Include invalid key
        merged = config.merge_cli_args(
            strategy="endowment", invalid_key="should_be_ignored", years=25
        )

        assert merged.strategy == "endowment"
        assert merged.years == 25
        # Invalid key should be ignored silently
        assert not hasattr(merged, "invalid_key")

    def test_guyton_klinger_config_example(self):
        """Test a realistic Guyton-Klinger configuration."""
        config = ConfigModel(
            strategy="guyton_klinger",
            years=35,
            paths=2000,
            init_balance=1500000.0,
            equity_pct=0.65,
            initial_rate=0.045,
            guard_pct=0.25,
            raise_pct=0.15,
            cut_pct=0.12,
            verbose=True,
            output="guyton_klinger_results.csv",
        )

        assert config.strategy == "guyton_klinger"
        assert config.initial_rate == 0.045
        assert config.guard_pct == 0.25
        assert config.raise_pct == 0.15
        assert config.cut_pct == 0.12
        assert config.output == "guyton_klinger_results.csv"

    def test_endowment_config_example(self):
        """Test a realistic endowment configuration."""
        config = ConfigModel(
            strategy="endowment",
            years=40,
            paths=5000,
            init_balance=2000000.0,
            equity_pct=0.8,
            alpha=0.75,
            beta=0.25,
            window=5,
            market_mode="bootstrap",
        )

        assert config.strategy == "endowment"
        assert config.alpha == 0.75
        assert config.beta == 0.25
        assert config.window == 5
        assert config.market_mode == "bootstrap"
        # Should pass alpha + beta validation
        assert abs(config.alpha + config.beta - 1.0) < 1e-10
