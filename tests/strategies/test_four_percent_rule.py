"""Tests for FourPercentRule strategy."""

import pytest

from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.strategies.four_percent_rule import FourPercentRule


class TestFourPercentRule:
    """Tests for FourPercentRule strategy."""

    def test_four_percent_rule_basic_withdrawal(self):
        """Test basic 4% withdrawal without inflation."""
        strategy = FourPercentRule()
        params = PortfolioParams(
            init_balance=1_000_000.0,
            equity_pct=0.6,
            fees_bps=50
        )
        
        # Without state, should return 4% of initial balance
        withdrawal = strategy.calculate_withdrawal(None, params)
        assert withdrawal == 40_000.0

    def test_four_percent_rule_with_inflation(self):
        """Test 4% withdrawal with inflation adjustment."""
        strategy = FourPercentRule()
        params = PortfolioParams(
            init_balance=1_000_000.0,
            equity_pct=0.6,
            fees_bps=50
        )
        state = YearState(
            year=2024,
            age=66,
            balance=950_000.0,
            inflation=0.03
        )
        
        # With 3% inflation, withdrawal should be 4% * (1 + 0.03) = 41,200
        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 41_200.0

    def test_four_percent_rule_with_zero_inflation(self):
        """Test 4% withdrawal with zero inflation."""
        strategy = FourPercentRule()
        params = PortfolioParams(
            init_balance=500_000.0,
            equity_pct=0.8,
            fees_bps=25
        )
        state = YearState(
            year=2024,
            age=65,
            balance=500_000.0,
            inflation=0.0
        )
        
        # With zero inflation, withdrawal should be exactly 4%
        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 20_000.0

    def test_four_percent_rule_with_negative_inflation(self):
        """Test 4% withdrawal with deflation (negative inflation)."""
        strategy = FourPercentRule()
        params = PortfolioParams(
            init_balance=1_000_000.0,
            equity_pct=0.6,
            fees_bps=50
        )
        state = YearState(
            year=2024,
            age=67,
            balance=1_100_000.0,
            inflation=-0.02  # 2% deflation
        )
        
        # With -2% inflation, withdrawal should be 4% * (1 - 0.02) = 39,200
        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 39_200.0

    def test_four_percent_rule_with_high_inflation(self):
        """Test 4% withdrawal with high inflation."""
        strategy = FourPercentRule()
        params = PortfolioParams(
            init_balance=2_000_000.0,
            equity_pct=0.7,
            fees_bps=75
        )
        state = YearState(
            year=2024,
            age=68,
            balance=1_800_000.0,
            inflation=0.08  # 8% inflation
        )
        
        # With 8% inflation, withdrawal should be 4% * (1 + 0.08) = 86,400
        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 86_400.0

    def test_four_percent_rule_different_initial_balances(self):
        """Test 4% rule with various initial balance amounts."""
        strategy = FourPercentRule()
        
        test_cases = [
            (100_000.0, 4_000.0),
            (250_000.0, 10_000.0),
            (750_000.0, 30_000.0),
            (1_500_000.0, 60_000.0),
            (50_000.0, 2_000.0),
        ]
        
        for init_balance, expected_withdrawal in test_cases:
            params = PortfolioParams(
                init_balance=init_balance,
                equity_pct=0.6,
                fees_bps=50
            )
            withdrawal = strategy.calculate_withdrawal(None, params)
            assert withdrawal == expected_withdrawal

    def test_four_percent_rule_str_representation(self):
        """Test string representation of FourPercentRule."""
        strategy = FourPercentRule()
        assert str(strategy) == "FourPercentRule"

    def test_four_percent_rule_repr_representation(self):
        """Test repr representation of FourPercentRule."""
        strategy = FourPercentRule()
        assert repr(strategy) == "FourPercentRule()"

    def test_four_percent_rule_inheritance(self):
        """Test that FourPercentRule properly inherits from BaseStrategy."""
        from capstone_finance.strategies.base import BaseStrategy
        
        strategy = FourPercentRule()
        assert isinstance(strategy, BaseStrategy)
        assert hasattr(strategy, 'calculate_withdrawal')

    def test_four_percent_rule_current_balance_ignored(self):
        """Test that current balance in state doesn't affect withdrawal calculation."""
        strategy = FourPercentRule()
        params = PortfolioParams(
            init_balance=1_000_000.0,
            equity_pct=0.6,
            fees_bps=50
        )
        
        # Test with different current balances but same inflation
        state1 = YearState(
            year=2024,
            age=65,
            balance=1_200_000.0,  # Higher balance
            inflation=0.02
        )
        state2 = YearState(
            year=2024,
            age=65,
            balance=800_000.0,   # Lower balance
            inflation=0.02
        )
        
        withdrawal1 = strategy.calculate_withdrawal(state1, params)
        withdrawal2 = strategy.calculate_withdrawal(state2, params)
        
        # Both should give same withdrawal (based on initial balance + inflation)
        assert withdrawal1 == withdrawal2
        assert withdrawal1 == 40_800.0  # 40,000 * 1.02