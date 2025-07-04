"""Guyton-Klinger Guardrails Strategy implementation.

This strategy implements dynamic withdrawal adjustments based on portfolio performance
using upper and lower guardrails. The withdrawal rate is adjusted when the portfolio
value crosses certain thresholds relative to the initial withdrawal amount.

Reference:
Guyton, J. T., & Klinger, W. J. (2006). Decision rules and maximum initial withdrawal rates.
Journal of Financial Planning, 19(3), 48-58.
"""

from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy


class GuytonKlingerStrategy(BaseStrategy):
    """Dynamic withdrawal strategy with guardrails.

    The Guyton-Klinger strategy adjusts withdrawals based on portfolio performance:
    - Increases withdrawals when portfolio performs well (upper guardrail)
    - Decreases withdrawals when portfolio underperforms (lower guardrail)
    - Implements prosperity rule: no cuts when portfolio > 120% of initial
    - Implements capital preservation rule: no raises when portfolio < 80% of initial

    Note: Due to the stateless nature of the base strategy interface, this implementation
    uses a simplified approach where guardrails are checked against the current portfolio
    value rather than a multi-year average. State tracking for cumulative inflation and
    portfolio history would require architectural changes to the simulation framework.

    Args:
        initial_rate: Initial withdrawal rate (default: 0.05 or 5%)
        guard_pct: Guardrail percentage from initial rate (default: 0.20 or 20%)
        raise_pct: Percentage increase when below lower guardrail (default: 0.10 or 10%)
        cut_pct: Percentage decrease when above upper guardrail (default: 0.10 or 10%)
    """

    def __init__(
        self,
        initial_rate: float = 0.05,
        guard_pct: float = 0.20,
        raise_pct: float = 0.10,
        cut_pct: float = 0.10,
    ):
        """Initialize Guyton-Klinger strategy with parameters.

        Args:
            initial_rate: Initial withdrawal rate
            guard_pct: Percentage deviation for guardrails (e.g., 0.20 = ±20%)
            raise_pct: Percentage to raise withdrawals when below lower guardrail
            cut_pct: Percentage to cut withdrawals when above upper guardrail
        """
        if not 0 < initial_rate < 1:
            raise ValueError("initial_rate must be between 0 and 1")
        if not 0 < guard_pct < 1:
            raise ValueError("guard_pct must be between 0 and 1")
        if not 0 < raise_pct < 1:
            raise ValueError("raise_pct must be between 0 and 1")
        if not 0 < cut_pct < 1:
            raise ValueError("cut_pct must be between 0 and 1")

        self.initial_rate = initial_rate
        self.guard_pct = guard_pct
        self.raise_pct = raise_pct
        self.cut_pct = cut_pct

        # Calculate guardrail thresholds
        self.upper_guardrail = initial_rate * (1 + guard_pct)
        self.lower_guardrail = initial_rate * (1 - guard_pct)

        # Track base withdrawal and cumulative inflation internally
        self._base_withdrawal: float | None = None
        self._cumulative_inflation: float = 1.0
        self._last_year: int | None = None

    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        """Calculate withdrawal amount based on guardrails.

        Args:
            state: Current year's financial state (if available)
            params: Portfolio parameters including initial balance

        Returns:
            Withdrawal amount for the current year
        """
        # Initialize base withdrawal on first call
        if self._base_withdrawal is None:
            self._base_withdrawal = params.init_balance * self.initial_rate

        # If no state provided, return base withdrawal
        if state is None:
            return self._base_withdrawal

        # Track cumulative inflation
        if self._last_year is None:
            # First year with state - apply inflation
            self._cumulative_inflation *= 1 + state.inflation
        elif state.year == self._last_year + 1:
            # Consecutive year - apply inflation
            self._cumulative_inflation *= 1 + state.inflation
        # Note: If years are not consecutive, we don't update cumulative inflation
        self._last_year = state.year

        # Start with inflation-adjusted base withdrawal
        inflation_adjusted_withdrawal = (
            self._base_withdrawal * self._cumulative_inflation
        )

        # Calculate current withdrawal rate
        current_balance = state.balance
        if current_balance <= 0:
            return 0.0

        current_rate = inflation_adjusted_withdrawal / current_balance

        # Determine if we need to adjust based on guardrails
        adjusted_withdrawal = inflation_adjusted_withdrawal

        # Check upper guardrail (reduce withdrawal)
        if current_rate > self.upper_guardrail:
            # Capital preservation rule: no cuts if portfolio > 120% of initial
            if current_balance <= params.init_balance * 1.2:
                # Apply cut
                adjusted_withdrawal = inflation_adjusted_withdrawal * (1 - self.cut_pct)
                # Update base withdrawal for future calculations
                self._base_withdrawal = adjusted_withdrawal / self._cumulative_inflation

        # Check lower guardrail (increase withdrawal)
        elif current_rate < self.lower_guardrail:
            # Prosperity rule: no raises if portfolio < 80% of initial
            if current_balance >= params.init_balance * 0.8:
                # Apply raise
                adjusted_withdrawal = inflation_adjusted_withdrawal * (
                    1 + self.raise_pct
                )
                # Update base withdrawal for future calculations
                self._base_withdrawal = adjusted_withdrawal / self._cumulative_inflation

        return adjusted_withdrawal

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"initial_rate={self.initial_rate}, "
            f"guard_pct={self.guard_pct}, "
            f"raise_pct={self.raise_pct}, "
            f"cut_pct={self.cut_pct})"
        )
