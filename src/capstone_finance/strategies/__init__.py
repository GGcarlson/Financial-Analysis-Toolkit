"""Withdrawal strategies for financial simulations."""

from .base import BaseStrategy
from .dummy import DummyStrategy

__all__ = ["BaseStrategy", "DummyStrategy"]