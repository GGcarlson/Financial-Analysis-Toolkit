"""Base class for withdrawal strategies."""

from abc import ABC, abstractmethod
from typing import Protocol

from ..core.models import PortfolioParams, YearState


class StateProtocol(Protocol):
    """Protocol for state objects that can be used with strategies."""
    year: int
    age: int
    balance: float
    inflation: float
    withdrawal_nominal: float | None


class BaseStrategy(ABC):
    """Abstract base class for withdrawal strategies.

    All withdrawal strategies must inherit from this class and implement
    the calculate_withdrawal method.
    """

    @abstractmethod
    def calculate_withdrawal(
        self, state: StateProtocol | None, params: PortfolioParams
    ) -> float:
        """Calculate withdrawal amount for the given year state.

        Args:
            state: Current year state including balance, age, inflation, etc.
                  Can be None for simple strategies that don't need state.
            params: Portfolio parameters including fees and allocation

        Returns:
            Withdrawal amount in nominal dollars for the year
        """
        pass

    def __str__(self) -> str:
        """Return strategy name for logging and debugging."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"{self.__class__.__name__}()"
