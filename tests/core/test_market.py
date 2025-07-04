"""Tests for the market simulator engine."""

import time

import numpy as np
import pandas as pd
import pytest

from capstone_finance.core import PortfolioParams
from capstone_finance.core.market import MarketSimulator, load_shiller_data


class TestMarketSimulator:
    """Tests for MarketSimulator class."""

    def test_initialization_lognormal(self):
        """Test initialization with log-normal mode."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        sim = MarketSimulator(params, mode="lognormal")

        assert sim.params == params
        assert sim.mode == "lognormal"
        assert isinstance(sim.rng, np.random.Generator)

    def test_initialization_bootstrap(self):
        """Test initialization with bootstrap mode."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        sim = MarketSimulator(params, mode="bootstrap")

        assert sim.params == params
        assert sim.mode == "bootstrap"
        assert hasattr(sim, "_historical_returns")
        assert hasattr(sim, "_block_returns")

    def test_invalid_mode(self):
        """Test that invalid mode raises appropriate error."""
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=50)
        # This should work with type checking but fail at runtime
        with pytest.raises((ValueError, KeyError, AttributeError)):
            sim = MarketSimulator(params, mode="invalid")  # type: ignore
            sim.generate(10, 10)

    def test_reproducibility_lognormal(self):
        """Test that same seed produces identical results for log-normal."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=12345
        )

        sim1 = MarketSimulator(params, mode="lognormal")
        returns1 = sim1.generate(100, 40)

        sim2 = MarketSimulator(params, mode="lognormal")
        returns2 = sim2.generate(100, 40)

        # Arrays should be identical bit-for-bit
        np.testing.assert_array_equal(returns1, returns2)

    def test_reproducibility_bootstrap(self):
        """Test that same seed produces identical results for bootstrap."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=12345
        )

        sim1 = MarketSimulator(params, mode="bootstrap")
        returns1 = sim1.generate(100, 40)

        sim2 = MarketSimulator(params, mode="bootstrap")
        returns2 = sim2.generate(100, 40)

        # Arrays should be identical bit-for-bit
        np.testing.assert_array_equal(returns1, returns2)

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        params1 = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=12345
        )
        params2 = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=54321
        )

        sim1 = MarketSimulator(params1, mode="lognormal")
        sim2 = MarketSimulator(params2, mode="lognormal")

        returns1 = sim1.generate(100, 40)
        returns2 = sim2.generate(100, 40)

        # Arrays should be different
        assert not np.array_equal(returns1, returns2)

    def test_output_shape(self):
        """Test that output has correct shape."""
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=50)
        sim = MarketSimulator(params)

        n_paths = 1000
        n_years = 30
        returns = sim.generate(n_paths, n_years)

        assert returns.shape == (n_paths, n_years)
        assert returns.dtype == np.float64

    def test_lognormal_statistics(self):
        """Test that log-normal returns have correct statistical properties."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        sim = MarketSimulator(params, mode="lognormal")

        # Generate large sample for statistical testing
        returns = sim.generate(10000, 40)

        # Calculate statistics
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Expected values
        expected_mean = 0.07  # 7%
        expected_std = 0.15  # 15%

        # Check within ±5% tolerance
        assert abs(mean_return - expected_mean) / expected_mean < 0.05
        assert abs(std_return - expected_std) / expected_std < 0.05

    def test_bootstrap_statistics(self):
        """Test that bootstrap returns have reasonable statistical properties."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        sim = MarketSimulator(params, mode="bootstrap")

        # Generate sample
        returns = sim.generate(1000, 40)

        # Check that returns are reasonable
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Bootstrap should produce returns in a reasonable range
        assert -0.5 < mean_return < 0.5  # Returns between -50% and +50%
        assert 0.01 < std_return < 0.5  # Volatility between 1% and 50%

    def test_bootstrap_with_non_divisible_years(self):
        """Test bootstrap mode with years not divisible by 5."""
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=50)
        sim = MarketSimulator(params, mode="bootstrap")

        # Test with 37 years (7 blocks of 5 + 2 remainder)
        returns = sim.generate(100, 37)
        assert returns.shape == (100, 37)

        # Test with 3 years (less than one block)
        returns = sim.generate(100, 3)
        assert returns.shape == (100, 3)

    @pytest.mark.performance
    def test_performance_requirement(self):
        """Test that simulator meets performance requirements."""
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=50)

        # Test both modes
        for mode in ["lognormal", "bootstrap"]:
            sim = MarketSimulator(params, mode=mode)

            # Warm-up run
            sim.generate(100, 10)

            # Timed run: 10,000 paths × 40 years
            start_time = time.time()
            returns = sim.generate(10000, 40)
            elapsed_time = time.time() - start_time

            # Should complete in less than 2 seconds
            assert (
                elapsed_time < 2.0
            ), f"{mode} mode took {elapsed_time:.2f}s (> 2s limit)"
            assert returns.shape == (10000, 40)

    def test_returns_are_finite(self):
        """Test that all generated returns are finite (no NaN or Inf)."""
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=50)

        for mode in ["lognormal", "bootstrap"]:
            sim = MarketSimulator(params, mode=mode)
            returns = sim.generate(1000, 40)

            assert np.all(
                np.isfinite(returns)
            ), f"{mode} mode produced non-finite values"

    def test_lognormal_returns_reasonable_range(self):
        """Test that log-normal returns are in a reasonable range."""
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=50)
        sim = MarketSimulator(params, mode="lognormal")
        returns = sim.generate(10000, 40)

        # Check that returns are reasonable (no extreme outliers)
        # With mu=0.07, sigma=0.15, 99.9% of returns should be within these bounds
        assert np.all(returns > -0.9), "Found returns below -90%"
        assert np.all(returns < 2.0), "Found returns above 200%"

        # Check that we have some variation
        assert np.min(returns) < -0.1, "No negative returns found"
        assert np.max(returns) > 0.2, "No high positive returns found"


class TestLoadShillerData:
    """Tests for load_shiller_data function."""

    def test_load_shiller_data_with_default_cache(self):
        """Test loading Shiller data with default cache directory."""
        result = load_shiller_data()

        # Currently returns empty DataFrame (placeholder implementation)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_load_shiller_data_with_custom_cache(self, tmp_path):
        """Test loading Shiller data with custom cache directory."""
        cache_dir = tmp_path / "custom_cache"
        result = load_shiller_data(cache_dir)

        # Should create cache directory
        assert cache_dir.exists()
        assert (cache_dir / "shiller_data.csv").exists() is False  # Not created yet

        # Currently returns empty DataFrame (placeholder implementation)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
