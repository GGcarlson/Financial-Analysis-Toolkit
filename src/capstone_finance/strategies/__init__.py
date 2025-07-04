"""Withdrawal strategies for financial simulations."""

from .base import BaseStrategy
from .dummy import DummyStrategy
from .four_percent_rule import FourPercentRule

__all__ = ["BaseStrategy", "DummyStrategy", "FourPercentRule"]