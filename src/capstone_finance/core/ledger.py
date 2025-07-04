"""Cash flow ledger for running financial simulations."""

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from ..strategies.base import BaseStrategy
from .market import MarketSimulator
from .models import PortfolioParams, YearState


class CashFlowLedger:
    """Cash flow ledger that orchestrates financial simulations.

    Manages the annual loop of withdrawals, fees, market returns, and taxes
    to produce complete simulation paths as YearState records.
    """

    def __init__(
        self,
        market_simulator: MarketSimulator,
        strategy: BaseStrategy,
        params: PortfolioParams,
        tax_engine: Callable[[float, float], float] | None = None,
    ):
        """Initialize the cash flow ledger.

        Args:
            market_simulator: Simulator for generating market returns
            strategy: Withdrawal strategy to use
            params: Portfolio parameters including initial balance and fees
            tax_engine: Optional tax calculation function that takes
                       (withdrawal_amount, balance) and returns tax owed.
                       Defaults to no-op (no taxes).
        """
        self.market_simulator = market_simulator
        self.strategy = strategy
        self.params = params
        self.tax_engine = tax_engine or self._no_tax

        # Cache fee factor for performance
        self._fee_factor = 1.0 - (params.fees_bps / 10000.0)

    def run(self, years: int, paths: int) -> list[list[YearState]]:
        """Run the simulation for the specified years and paths.

        Args:
            years: Number of years to simulate
            paths: Number of simulation paths to run

        Returns:
            List of paths, where each path is a list of YearState records
        """
        # Generate all market returns upfront for performance
        returns = self.market_simulator.generate(paths, years)

        # Pre-allocate result structure
        results: list[list[YearState]] = []

        # Starting values
        initial_balance = self.params.init_balance
        starting_age = 65  # Default starting age - could be parameterized
        starting_year = 2024  # Default starting year - could be parameterized

        # Run simulation for each path
        for path_idx in range(paths):
            path_results = []
            balance = initial_balance

            for year_idx in range(years):
                current_year = starting_year + year_idx
                current_age = starting_age + year_idx
                market_return = returns[path_idx, year_idx]

                # Create minimal state for strategy calculation (avoid unnecessary object creation)
                # Most strategies only need balance and age
                if (
                    hasattr(self.strategy, "_needs_full_state")
                    and self.strategy._needs_full_state
                ):
                    current_state = YearState(
                        year=current_year,
                        age=current_age,
                        balance=balance,
                        inflation=0.0,
                        withdrawal_nominal=None,
                    )
                    withdrawal = self.strategy.calculate_withdrawal(
                        current_state, self.params
                    )
                else:
                    # For simple strategies like DummyStrategy, avoid creating YearState
                    withdrawal = self.strategy.calculate_withdrawal(None, self.params)

                # Apply withdrawal
                balance -= withdrawal

                # Apply taxes on withdrawal if tax engine provided
                if withdrawal > 0:
                    tax_owed = self.tax_engine(withdrawal, balance)
                    balance -= tax_owed

                # Apply annual fees and market return in one step
                balance = max(0.0, balance * self._fee_factor * (1.0 + market_return))

                # Create final state record for this year
                year_state = YearState(
                    year=current_year,
                    age=current_age,
                    balance=balance,
                    inflation=0.0,  # Placeholder - inflation handling TBD
                    withdrawal_nominal=withdrawal,
                )

                path_results.append(year_state)

            results.append(path_results)

        return results

    @staticmethod
    def _no_tax(withdrawal_amount: float, balance: float) -> float:
        """Default no-op tax engine that returns zero tax.

        Args:
            withdrawal_amount: Amount withdrawn (unused)
            balance: Current balance (unused)

        Returns:
            Always returns 0.0 (no tax)
        """
        return 0.0


def run_simulation_vectorized(
    market_simulator: MarketSimulator,
    strategy: BaseStrategy,
    params: PortfolioParams,
    years: int,
    paths: int,
    tax_engine: Callable[[float, float], float] | None = None,
) -> NDArray[np.float64]:
    """Vectorized simulation runner for performance-critical applications.

    This is an optimized version that returns only final balances as a numpy array
    instead of full YearState objects, for maximum performance.

    Args:
        market_simulator: Simulator for generating market returns
        strategy: Withdrawal strategy to use
        params: Portfolio parameters
        years: Number of years to simulate
        paths: Number of simulation paths
        tax_engine: Optional tax calculation function

    Returns:
        Array of shape (paths, years) containing balance evolution
    """
    # Generate all market returns upfront
    returns = market_simulator.generate(paths, years)

    # Pre-allocate result array
    balances = np.zeros((paths, years), dtype=np.float64)

    # Starting values
    initial_balance = params.init_balance
    fee_factor = 1.0 - (params.fees_bps / 10000.0)
    starting_age = 65
    starting_year = 2024

    # Tax engine or no-op
    if tax_engine is None:

        def tax_engine(w, b):
            return 0.0

    for path_idx in range(paths):
        balance = initial_balance

        for year_idx in range(years):
            current_year = starting_year + year_idx
            current_age = starting_age + year_idx
            market_return = returns[path_idx, year_idx]

            # Create current state for strategy
            current_state = YearState(
                year=current_year,
                age=current_age,
                balance=balance,
                inflation=0.0,
                withdrawal_nominal=None,
            )

            # Calculate withdrawal
            withdrawal = strategy.calculate_withdrawal(current_state, params)

            # Apply withdrawal and taxes
            balance -= withdrawal
            if withdrawal > 0:
                balance -= tax_engine(withdrawal, balance)

            # Apply fees and market return
            balance = balance * fee_factor * (1.0 + market_return)
            balance = max(0.0, balance)

            balances[path_idx, year_idx] = balance

    return balances
