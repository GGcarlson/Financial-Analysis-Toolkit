"""Endowment (Moving-Average) withdrawal strategy implementation."""

from collections import deque

from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy


class EndowmentStrategy(BaseStrategy):
    """Endowment withdrawal strategy using Yale's moving-average formula.

    Implements the Yale endowment approach:
    withdrawal = alpha * current_portfolio + beta * moving_average(portfolio, window)

    This strategy smooths withdrawals by considering both current portfolio value
    and the historical moving average, reducing volatility compared to strategies
    that only look at current value.
    """

    def __init__(self, alpha: float = 0.7, beta: float = 0.3, window: int = 3) -> None:
        """Initialize the endowment strategy.

        Args:
            alpha: Weight for current portfolio value (default 0.7)
            beta: Weight for moving average (default 0.3)
            window: Number of years for moving average calculation (default 3)

        Raises:
            ValueError: If parameters are invalid
        """
        if alpha < 0 or alpha > 1:
            raise ValueError("Alpha must be between 0 and 1")
        if beta < 0 or beta > 1:
            raise ValueError("Beta must be between 0 and 1")
        if abs(alpha + beta - 1.0) > 1e-10:
            raise ValueError("Alpha + Beta must equal 1.0")
        if window < 1:
            raise ValueError("Window must be at least 1")

        self.alpha = alpha
        self.beta = beta
        self.window = window
        self.portfolio_history: deque[float] = deque(maxlen=window)

    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        """Calculate endowment withdrawal using Yale formula.

        Args:
            state: Current year state including current balance
            params: Portfolio parameters including initial balance

        Returns:
            Withdrawal amount using Yale endowment formula
        """
        if state is None:
            # If no state provided, use initial balance and initialize history
            current_balance = params.init_balance
            self.portfolio_history.clear()
            self.portfolio_history.append(current_balance)
        else:
            current_balance = state.balance
            # Add current balance to history
            self.portfolio_history.append(current_balance)

        # Calculate moving average of portfolio values
        if len(self.portfolio_history) == 0:
            moving_average = current_balance
        else:
            moving_average = sum(self.portfolio_history) / len(self.portfolio_history)

        # Apply Yale formula: alpha * current + beta * moving_average
        withdrawal = self.alpha * current_balance + self.beta * moving_average

        return withdrawal

    def __str__(self) -> str:
        """Return strategy name for logging and debugging."""
        return f"EndowmentStrategy(α={self.alpha:.1f},β={self.beta:.1f},window={self.window})"

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"EndowmentStrategy(alpha={self.alpha}, beta={self.beta}, "
            f"window={self.window})"
        )

    def reset_history(self) -> None:
        """Reset the portfolio history.

        Useful for testing or when starting a new simulation sequence.
        """
        self.portfolio_history.clear()
