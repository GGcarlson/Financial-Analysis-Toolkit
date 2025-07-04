"""Constant percentage withdrawal strategy implementation."""

from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy


class ConstantPercentageStrategy(BaseStrategy):
    """Constant percentage withdrawal strategy.

    Withdraws a fixed percentage of the current portfolio balance each year,
    unlike the 4% rule which adjusts the initial withdrawal for inflation.
    This strategy is more dynamic - withdrawals increase/decrease with
    portfolio performance.
    """

    def __init__(self, percentage: float = 0.05) -> None:
        """Initialize the constant percentage strategy.

        Args:
            percentage: The percentage of current balance to withdraw each year
                       (default 0.05 = 5%)
        """
        if percentage < 0:
            raise ValueError("Percentage must be non-negative")
        if percentage > 1:
            raise ValueError("Percentage must be <= 1.0 (100%)")

        self.percentage = percentage

    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        """Calculate constant percentage withdrawal amount.

        Args:
            state: Current year state including current balance
            params: Portfolio parameters including initial balance

        Returns:
            Withdrawal amount: percentage of current balance
        """
        if state is None:
            # If no state provided, use initial balance
            return params.init_balance * self.percentage

        # Withdraw fixed percentage of current balance
        return state.balance * self.percentage

    def __str__(self) -> str:
        """Return strategy name for logging and debugging."""
        return f"ConstantPercentageStrategy({self.percentage:.1%})"

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"ConstantPercentageStrategy(percentage={self.percentage})"
