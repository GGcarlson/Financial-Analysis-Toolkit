"""Dummy strategy for testing purposes."""

from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy


class DummyStrategy(BaseStrategy):
    """Dummy withdrawal strategy that returns 0% withdrawal.

    This strategy is used for testing baseline scenarios where
    no withdrawals are made, allowing verification of balance
    calculations with only market returns and fees.
    """

    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        """Return zero withdrawal amount.

        Args:
            state: Current year state (unused in dummy strategy, can be None)
            params: Portfolio parameters (unused in dummy strategy)

        Returns:
            Always returns 0.0 (no withdrawal)
        """
        return 0.0

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return "DummyStrategy(withdrawal_rate=0.0)"
