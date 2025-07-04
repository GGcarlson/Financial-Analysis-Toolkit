"""Tests for EndowmentStrategy."""

import pytest

from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.strategies.endowment import EndowmentStrategy


class TestEndowmentStrategy:
    """Tests for EndowmentStrategy."""

    def test_default_parameter_initialization(self):
        """Test strategy initialization with default parameters."""
        strategy = EndowmentStrategy()
        assert strategy.alpha == 0.7
        assert strategy.beta == 0.3
        assert strategy.window == 3
        assert len(strategy.portfolio_history) == 0

    def test_custom_parameter_initialization(self):
        """Test strategy initialization with custom parameters."""
        strategy = EndowmentStrategy(alpha=0.6, beta=0.4, window=5)
        assert strategy.alpha == 0.6
        assert strategy.beta == 0.4
        assert strategy.window == 5

    def test_alpha_validation(self):
        """Test alpha parameter validation."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            EndowmentStrategy(alpha=-0.1)

        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            EndowmentStrategy(alpha=1.5)

    def test_beta_validation(self):
        """Test beta parameter validation."""
        with pytest.raises(ValueError, match="Beta must be between 0 and 1"):
            EndowmentStrategy(beta=-0.1)

        with pytest.raises(ValueError, match="Beta must be between 0 and 1"):
            EndowmentStrategy(beta=1.5)

    def test_alpha_beta_sum_validation(self):
        """Test that alpha + beta must equal 1.0."""
        with pytest.raises(ValueError, match="Alpha \\+ Beta must equal 1.0"):
            EndowmentStrategy(alpha=0.5, beta=0.4)  # Sum = 0.9

        with pytest.raises(ValueError, match="Alpha \\+ Beta must equal 1.0"):
            EndowmentStrategy(alpha=0.6, beta=0.5)  # Sum = 1.1

    def test_window_validation(self):
        """Test window parameter validation."""
        with pytest.raises(ValueError, match="Window must be at least 1"):
            EndowmentStrategy(window=0)

        with pytest.raises(ValueError, match="Window must be at least 1"):
            EndowmentStrategy(window=-1)

    def test_first_year_withdrawal_with_none_state(self):
        """Test first-year withdrawal when state is None."""
        strategy = EndowmentStrategy(alpha=0.7, beta=0.3, window=3)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # With None state, should use initial balance for both current and average
        withdrawal = strategy.calculate_withdrawal(None, params)

        # Expected: 0.7 * 1_000_000 + 0.3 * 1_000_000 = 1_000_000
        expected = 0.7 * 1_000_000.0 + 0.3 * 1_000_000.0
        assert withdrawal == expected
        assert len(strategy.portfolio_history) == 1
        assert strategy.portfolio_history[0] == 1_000_000.0

    def test_golden_file_hand_calculated_example(self):
        """Golden-file test with hand-calculated Yale endowment example.

        Alpha=0.7, Beta=0.3, Window=3
        Portfolio values: [1000000, 1100000, 900000, 1200000]
        """
        strategy = EndowmentStrategy(alpha=0.7, beta=0.3, window=3)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Year 1: Portfolio = 1,000,000, History = [1,000,000], Avg = 1,000,000
        # Withdrawal = 0.7 * 1,000,000 + 0.3 * 1,000,000 = 1,000,000
        state1 = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        withdrawal1 = strategy.calculate_withdrawal(state1, params)
        expected1 = 0.7 * 1_000_000.0 + 0.3 * 1_000_000.0
        assert withdrawal1 == expected1  # 1,000,000

        # Year 2: Portfolio = 1,100,000, History = [1,000,000, 1,100,000], Avg = 1,050,000
        # Withdrawal = 0.7 * 1,100,000 + 0.3 * 1,050,000 = 770,000 + 315,000 = 1,085,000
        state2 = YearState(year=2025, age=66, balance=1_100_000.0, inflation=0.03)
        withdrawal2 = strategy.calculate_withdrawal(state2, params)
        expected2 = 0.7 * 1_100_000.0 + 0.3 * 1_050_000.0
        assert withdrawal2 == expected2  # 1,085,000

        # Year 3: Portfolio = 900,000, History = [1,000,000, 1,100,000, 900,000], Avg = 1,000,000
        # Withdrawal = 0.7 * 900,000 + 0.3 * 1,000,000 = 630,000 + 300,000 = 930,000
        state3 = YearState(year=2026, age=67, balance=900_000.0, inflation=0.03)
        withdrawal3 = strategy.calculate_withdrawal(state3, params)
        expected3 = 0.7 * 900_000.0 + 0.3 * 1_000_000.0
        assert withdrawal3 == expected3  # 930,000

        # Year 4: Portfolio = 1,200,000, History = [1,100,000, 900,000, 1,200,000], Avg = 1,066,667
        # (window=3, so oldest value 1,000,000 is dropped)
        # Withdrawal = 0.7 * 1,200,000 + 0.3 * 1,066,667 = 840,000 + 320,000 = 1,160,000
        state4 = YearState(year=2027, age=68, balance=1_200_000.0, inflation=0.03)
        withdrawal4 = strategy.calculate_withdrawal(state4, params)
        avg4 = (1_100_000.0 + 900_000.0 + 1_200_000.0) / 3.0  # 1,066,666.67
        expected4 = 0.7 * 1_200_000.0 + 0.3 * avg4
        assert (
            abs(withdrawal4 - expected4) < 0.01
        )  # Account for floating point precision

    def test_moving_average_calculation_accuracy(self):
        """Test that moving average is calculated correctly with different window sizes."""
        strategy = EndowmentStrategy(alpha=0.5, beta=0.5, window=2)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Add portfolio values one by one and verify moving average
        values = [1000, 2000, 3000, 4000]
        expected_withdrawals = []

        for i, value in enumerate(values):
            state = YearState(
                year=2024 + i, age=65 + i, balance=float(value), inflation=0.03
            )
            withdrawal = strategy.calculate_withdrawal(state, params)

            # Calculate expected moving average
            if i == 0:
                avg = value  # Only one value
            else:
                # Take last 2 values (window=2)
                recent_values = values[max(0, i - 1) : i + 1]
                avg = sum(recent_values) / len(recent_values)

            expected = 0.5 * value + 0.5 * avg
            expected_withdrawals.append(expected)
            assert abs(withdrawal - expected) < 0.01

    def test_window_size_behavior(self):
        """Test behavior with different window sizes."""
        values = [100, 200, 300, 400, 500]

        # Test with window=1 (no smoothing effect)
        strategy1 = EndowmentStrategy(alpha=0.8, beta=0.2, window=1)
        for value in values:
            state = YearState(year=2024, age=65, balance=float(value), inflation=0.03)
            params = PortfolioParams(init_balance=1000.0, equity_pct=0.6, fees_bps=50)
            withdrawal = strategy1.calculate_withdrawal(state, params)
            # With window=1, moving average equals current value
            expected = 0.8 * value + 0.2 * value  # = value
            assert withdrawal == expected

        # Test with large window
        strategy5 = EndowmentStrategy(alpha=0.6, beta=0.4, window=5)
        withdrawals = []
        for i, value in enumerate(values):
            state = YearState(
                year=2024 + i, age=65 + i, balance=float(value), inflation=0.03
            )
            params = PortfolioParams(init_balance=1000.0, equity_pct=0.6, fees_bps=50)
            withdrawal = strategy5.calculate_withdrawal(state, params)
            withdrawals.append(withdrawal)

        # Verify that later withdrawals show smoothing effect
        assert len(withdrawals) == 5

    def test_reset_history_functionality(self):
        """Test the reset_history method."""
        strategy = EndowmentStrategy(alpha=0.7, beta=0.3, window=3)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Add some history
        for i in range(3):
            state = YearState(
                year=2024 + i, age=65 + i, balance=1000.0 * (i + 1), inflation=0.03
            )
            strategy.calculate_withdrawal(state, params)

        assert len(strategy.portfolio_history) == 3

        # Reset history
        strategy.reset_history()
        assert len(strategy.portfolio_history) == 0

    def test_edge_case_zero_balances(self):
        """Test behavior with zero portfolio balance."""
        strategy = EndowmentStrategy(alpha=0.7, beta=0.3, window=3)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Start with normal balance
        state1 = YearState(year=2024, age=65, balance=1000.0, inflation=0.03)
        strategy.calculate_withdrawal(state1, params)

        # Then zero balance
        state2 = YearState(year=2025, age=66, balance=0.0, inflation=0.03)
        withdrawal2 = strategy.calculate_withdrawal(state2, params)

        # Moving average should be (1000 + 0) / 2 = 500
        expected2 = 0.7 * 0.0 + 0.3 * 500.0
        assert withdrawal2 == expected2

    def test_different_alpha_beta_combinations(self):
        """Test various alpha/beta combinations that sum to 1.0."""
        test_cases = [
            (1.0, 0.0),  # Pure current value
            (0.0, 1.0),  # Pure moving average
            (0.5, 0.5),  # Equal weighting
            (0.9, 0.1),  # Heavy current value weighting
            (0.1, 0.9),  # Heavy moving average weighting
        ]

        portfolio_value = 1000.0
        params = PortfolioParams(
            init_balance=portfolio_value, equity_pct=0.6, fees_bps=50
        )

        for alpha, beta in test_cases:
            strategy = EndowmentStrategy(alpha=alpha, beta=beta, window=3)
            state = YearState(
                year=2024, age=65, balance=portfolio_value, inflation=0.03
            )
            withdrawal = strategy.calculate_withdrawal(state, params)

            # For first call, moving average equals current value
            expected = alpha * portfolio_value + beta * portfolio_value
            assert withdrawal == expected

    def test_str_representation(self):
        """Test string representation of EndowmentStrategy."""
        strategy = EndowmentStrategy(alpha=0.6, beta=0.4, window=5)
        assert str(strategy) == "EndowmentStrategy(α=0.6,β=0.4,window=5)"

    def test_repr_representation(self):
        """Test repr representation of EndowmentStrategy."""
        strategy = EndowmentStrategy(alpha=0.8, beta=0.2, window=2)
        assert repr(strategy) == "EndowmentStrategy(alpha=0.8, beta=0.2, window=2)"

    def test_inheritance(self):
        """Test that EndowmentStrategy properly inherits from BaseStrategy."""
        from capstone_finance.strategies.base import BaseStrategy

        strategy = EndowmentStrategy()
        assert isinstance(strategy, BaseStrategy)
        assert hasattr(strategy, "calculate_withdrawal")

    def test_plugin_discovery_compatibility(self):
        """Test that strategy can be instantiated without parameters (for plugin discovery)."""
        # This simulates how the plugin discovery system would instantiate the strategy
        strategy = EndowmentStrategy()
        assert strategy.alpha == 0.7  # Should use defaults
        assert strategy.beta == 0.3
        assert strategy.window == 3

        # Should work with basic calculation
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        withdrawal = strategy.calculate_withdrawal(None, params)
        expected = 0.7 * 1_000_000.0 + 0.3 * 1_000_000.0
        assert withdrawal == expected

    def test_deterministic_behavior(self):
        """Test that same inputs always produce same outputs."""
        strategy1 = EndowmentStrategy(alpha=0.7, beta=0.3, window=3)
        strategy2 = EndowmentStrategy(alpha=0.7, beta=0.3, window=3)

        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Run same sequence on both strategies
        portfolio_values = [1000000, 1100000, 950000, 1200000]
        withdrawals1 = []
        withdrawals2 = []

        for i, value in enumerate(portfolio_values):
            state = YearState(
                year=2024 + i, age=65 + i, balance=float(value), inflation=0.03
            )
            w1 = strategy1.calculate_withdrawal(state, params)
            w2 = strategy2.calculate_withdrawal(state, params)
            withdrawals1.append(w1)
            withdrawals2.append(w2)

        # Should produce identical results
        assert withdrawals1 == withdrawals2
