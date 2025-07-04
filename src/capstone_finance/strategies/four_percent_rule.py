"""4% Rule withdrawal strategy implementation."""

from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy


class FourPercentRule(BaseStrategy):
    """4% Rule withdrawal strategy (Bengen method).

    Classic fixed withdrawal rate strategy that withdraws 4% of the initial
    portfolio balance in the first year, then adjusts subsequent withdrawals
    for inflation to maintain constant purchasing power.
    """

    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        """Calculate 4% rule withdrawal amount.

        Args:
            state: Current year state including inflation data
            params: Portfolio parameters including initial balance

        Returns:
            Withdrawal amount: 4% of initial balance adjusted for inflation
        """
        base_withdrawal = params.init_balance * 0.04

        if state is None:
            return base_withdrawal

        # Adjust for inflation to maintain purchasing power
        return base_withdrawal * (1 + state.inflation)
