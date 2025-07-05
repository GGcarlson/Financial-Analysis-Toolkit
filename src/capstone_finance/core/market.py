"""Market simulator engine for generating return paths.

Supports both log-normal and bootstrap (historical) return generation modes.
Optimized for high performance with vectorized operations.
"""

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .models import PortfolioParams


class MarketSimulator:
    """High-performance market return simulator.

    Generates annual real returns using either log-normal distribution
    or bootstrap sampling from historical data.
    """

    def __init__(
        self,
        params: PortfolioParams,
        mode: Literal["lognormal", "bootstrap"] = "lognormal",
    ):
        """Initialize the market simulator.

        Args:
            params: Portfolio parameters including RNG seed
            mode: Generation mode - 'lognormal' or 'bootstrap'
        """
        self.params = params
        self.mode = mode
        self.rng = np.random.Generator(np.random.PCG64(params.seed))

        # Mode-specific initialization
        if mode == "bootstrap":
            self._historical_returns = self._load_historical_data()
            self._prepare_bootstrap_data()

    def generate(self, n_paths: int, n_years: int) -> NDArray[np.float64]:
        """Generate annual real returns.

        Args:
            n_paths: Number of simulation paths
            n_years: Number of years to simulate

        Returns:
            Array of shape (n_paths, n_years) containing annual real returns
        """
        if self.mode == "lognormal":
            return self._generate_lognormal(n_paths, n_years)
        else:  # bootstrap
            return self._generate_bootstrap(n_paths, n_years)

    def _generate_lognormal(self, n_paths: int, n_years: int) -> NDArray[np.float64]:
        """Generate returns using log-normal distribution.

        Uses μ = 7%, σ = 15% real returns.
        """
        mu = 0.07  # 7% real return
        sigma = 0.15  # 15% volatility

        # Generate all random numbers at once for performance
        # For simple annual returns with mean mu and std sigma:
        # R = mu + sigma * Z
        z = self.rng.standard_normal((n_paths, n_years))
        returns = mu + sigma * z

        return returns

    def _generate_bootstrap(self, n_paths: int, n_years: int) -> NDArray[np.float64]:
        """Generate returns using bootstrap sampling from historical data.

        Samples 5-year rolling windows from historical returns.
        """
        # Number of 5-year blocks needed
        blocks_per_path = n_years // 5
        remainder_years = n_years % 5

        # Pre-allocate output array
        returns = np.zeros((n_paths, n_years), dtype=np.float64)

        # Generate block indices for all paths at once
        n_blocks = len(self._block_returns)
        block_indices = self.rng.integers(0, n_blocks, size=(n_paths, blocks_per_path))

        # Fill in the returns using vectorized operations
        for i in range(blocks_per_path):
            start_idx = i * 5
            end_idx = start_idx + 5
            # Use advanced indexing to select blocks for all paths at once
            returns[:, start_idx:end_idx] = self._block_returns[block_indices[:, i]]

        # Handle remainder years if n_years is not divisible by 5
        if remainder_years > 0:
            # Sample individual years for the remainder
            all_years = self._historical_returns.flatten()
            remainder_indices = self.rng.integers(
                0, len(all_years), size=(n_paths, remainder_years)
            )
            returns[:, -remainder_years:] = all_years[remainder_indices]

        return returns

    def _load_historical_data(self) -> NDArray[np.float64]:
        """Load historical return data.

        For now, returns synthetic data matching Shiller characteristics.
        TODO: Implement actual Shiller data loading.
        """
        # Create synthetic historical data for now
        # This matches approximate characteristics of Shiller data
        # Real implementation would load actual Shiller CAPE data
        np.random.seed(12345)  # Fixed seed for consistent synthetic data

        # Generate 100 years of historical returns
        # Using parameters that roughly match historical S&P 500
        years = 100
        annual_returns = np.random.normal(0.07, 0.18, years)

        return annual_returns

    def _prepare_bootstrap_data(self) -> None:
        """Prepare 5-year rolling windows for efficient bootstrap sampling."""
        returns = self._historical_returns
        n_years = len(returns)

        # Create all possible 5-year blocks
        n_blocks = n_years - 4  # Number of possible 5-year windows
        self._block_returns = np.array([returns[i : i + 5] for i in range(n_blocks)])


def load_shiller_data(cache_dir: Path | None = None) -> pd.DataFrame:
    """Load Shiller CAPE data with caching.

    Args:
        cache_dir: Directory for caching data. Defaults to ~/.capstone_finance/cache

    Returns:
        DataFrame with Shiller data including real returns
    """
    if cache_dir is None:
        cache_dir = Path.home() / ".capstone_finance" / "cache"

    cache_dir.mkdir(parents=True, exist_ok=True)
    # cache_file = cache_dir / "shiller_data.csv"  # TODO: Future implementation

    # For now, return empty DataFrame
    # TODO: Implement actual Shiller data fetching
    return pd.DataFrame()
