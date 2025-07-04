"""Tests for ConstantPercentageStrategy."""

import pytest

from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.strategies.constant_percentage import ConstantPercentageStrategy


class TestConstantPercentageStrategy:
    """Tests for ConstantPercentageStrategy."""

    def test_default_percentage_initialization(self):
        """Test strategy initialization with default percentage."""
        strategy = ConstantPercentageStrategy()
        assert strategy.percentage == 0.05  # 5% default

    def test_custom_percentage_initialization(self):
        """Test strategy initialization with custom percentage."""
        strategy = ConstantPercentageStrategy(percentage=0.03)
        assert strategy.percentage == 0.03

    def test_negative_percentage_raises_error(self):
        """Test that negative percentage raises ValueError."""
        with pytest.raises(ValueError, match="Percentage must be non-negative"):
            ConstantPercentageStrategy(percentage=-0.01)

    def test_percentage_over_one_raises_error(self):
        """Test that percentage > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Percentage must be <= 1.0"):
            ConstantPercentageStrategy(percentage=1.5)

    def test_first_year_withdrawal_with_none_state(self):
        """Test first-year withdrawal equals init_balance * percent when state is None."""
        strategy = ConstantPercentageStrategy(percentage=0.05)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Without state, should return 5% of initial balance
        withdrawal = strategy.calculate_withdrawal(None, params)
        assert withdrawal == 50_000.0  # 1,000,000 * 0.05

    def test_withdrawal_tracks_current_balance(self):
        """Test that withdrawal tracks current balance changes."""
        strategy = ConstantPercentageStrategy(percentage=0.04)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Test with different current balances
        state1 = YearState(
            year=2024, age=65, balance=1_200_000.0, inflation=0.03  # Portfolio grew
        )
        withdrawal1 = strategy.calculate_withdrawal(state1, params)
        assert withdrawal1 == 48_000.0  # 1,200,000 * 0.04

        state2 = YearState(
            year=2025, age=66, balance=800_000.0, inflation=0.03  # Portfolio declined
        )
        withdrawal2 = strategy.calculate_withdrawal(state2, params)
        assert withdrawal2 == 32_000.0  # 800,000 * 0.04

    def test_different_percentage_values(self):
        """Test strategy with various percentage values."""
        test_cases = [
            (0.03, 1_000_000.0, 30_000.0),  # 3%
            (0.05, 500_000.0, 25_000.0),  # 5%
            (0.07, 2_000_000.0, 140_000.0),  # 7%
            (0.10, 250_000.0, 25_000.0),  # 10%
        ]

        for percentage, balance, expected_withdrawal in test_cases:
            strategy = ConstantPercentageStrategy(percentage=percentage)
            state = YearState(year=2024, age=65, balance=balance, inflation=0.02)
            params = PortfolioParams(
                init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50
            )

            withdrawal = strategy.calculate_withdrawal(state, params)
            assert withdrawal == expected_withdrawal

    def test_zero_percentage(self):
        """Test strategy with 0% withdrawal rate."""
        strategy = ConstantPercentageStrategy(percentage=0.0)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=65, balance=1_500_000.0, inflation=0.03)

        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 0.0

    def test_withdrawal_ignores_inflation(self):
        """Test that withdrawal calculation ignores inflation (unlike 4% rule)."""
        strategy = ConstantPercentageStrategy(percentage=0.05)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Test with different inflation rates but same balance
        state_low_inflation = YearState(
            year=2024, age=65, balance=1_000_000.0, inflation=0.01  # 1% inflation
        )
        state_high_inflation = YearState(
            year=2024, age=65, balance=1_000_000.0, inflation=0.08  # 8% inflation
        )

        withdrawal1 = strategy.calculate_withdrawal(state_low_inflation, params)
        withdrawal2 = strategy.calculate_withdrawal(state_high_inflation, params)

        # Both should be the same (5% of balance)
        assert withdrawal1 == withdrawal2 == 50_000.0

    def test_withdrawal_ignores_initial_balance(self):
        """Test that withdrawal calculation ignores initial balance when state provided."""
        strategy = ConstantPercentageStrategy(percentage=0.06)

        # Different initial balances
        params1 = PortfolioParams(
            init_balance=500_000.0, equity_pct=0.6, fees_bps=50  # Smaller initial
        )
        params2 = PortfolioParams(
            init_balance=2_000_000.0, equity_pct=0.6, fees_bps=50  # Larger initial
        )

        # Same current balance
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.02)

        withdrawal1 = strategy.calculate_withdrawal(state, params1)
        withdrawal2 = strategy.calculate_withdrawal(state, params2)

        # Both should be same (6% of current balance)
        assert withdrawal1 == withdrawal2 == 60_000.0

    def test_str_representation(self):
        """Test string representation of ConstantPercentageStrategy."""
        strategy = ConstantPercentageStrategy(percentage=0.045)
        assert str(strategy) == "ConstantPercentageStrategy(4.5%)"

    def test_repr_representation(self):
        """Test repr representation of ConstantPercentageStrategy."""
        strategy = ConstantPercentageStrategy(percentage=0.075)
        assert repr(strategy) == "ConstantPercentageStrategy(percentage=0.075)"

    def test_inheritance(self):
        """Test that ConstantPercentageStrategy properly inherits from BaseStrategy."""
        from capstone_finance.strategies.base import BaseStrategy

        strategy = ConstantPercentageStrategy()
        assert isinstance(strategy, BaseStrategy)
        assert hasattr(strategy, "calculate_withdrawal")

    def test_edge_case_very_small_balance(self):
        """Test withdrawal calculation with very small balance."""
        strategy = ConstantPercentageStrategy(percentage=0.05)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(
            year=2024, age=65, balance=100.0, inflation=0.03  # Very small balance
        )

        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 5.0  # 100 * 0.05

    def test_edge_case_zero_balance(self):
        """Test withdrawal calculation with zero balance."""
        strategy = ConstantPercentageStrategy(percentage=0.05)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(
            year=2024, age=65, balance=0.0, inflation=0.03  # Zero balance
        )

        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 0.0  # 0 * 0.05

    def test_maximum_percentage(self):
        """Test strategy with 100% withdrawal rate."""
        strategy = ConstantPercentageStrategy(percentage=1.0)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=65, balance=750_000.0, inflation=0.03)

        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 750_000.0  # 100% of balance

    def test_plugin_discovery_compatibility(self):
        """Test that strategy can be instantiated without parameters (for plugin discovery)."""
        # This simulates how the plugin discovery system would instantiate the strategy
        strategy = ConstantPercentageStrategy()
        assert strategy.percentage == 0.05  # Should use default

        # Should work with basic calculation
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        withdrawal = strategy.calculate_withdrawal(None, params)
        assert withdrawal == 50_000.0
