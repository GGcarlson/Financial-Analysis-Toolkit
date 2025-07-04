"""Unit tests for the Guyton-Klinger Guardrails Strategy."""

import pytest

from capstone_finance import YearState
from capstone_finance.core.models import PortfolioParams
from capstone_finance.strategies.guyton_klinger import GuytonKlingerStrategy


class TestGuytonKlingerStrategy:
    """Test cases for Guyton-Klinger strategy implementation."""

    def test_initialization_valid_parameters(self):
        """Test strategy initialization with valid parameters."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.04, guard_pct=0.25, raise_pct=0.15, cut_pct=0.08
        )
        assert strategy.initial_rate == 0.04
        assert strategy.guard_pct == 0.25
        assert strategy.raise_pct == 0.15
        assert strategy.cut_pct == 0.08
        assert strategy.upper_guardrail == 0.04 * 1.25  # 0.05
        assert strategy.lower_guardrail == 0.04 * 0.75  # 0.03

    def test_initialization_default_parameters(self):
        """Test strategy initialization with default parameters."""
        strategy = GuytonKlingerStrategy()
        assert strategy.initial_rate == 0.05
        assert strategy.guard_pct == 0.20
        assert strategy.raise_pct == 0.10
        assert strategy.cut_pct == 0.10
        assert strategy.upper_guardrail == 0.05 * 1.20  # 0.06
        assert strategy.lower_guardrail == 0.05 * 0.80  # 0.04

    def test_initialization_invalid_parameters(self):
        """Test strategy initialization with invalid parameters."""
        # Invalid initial rate
        with pytest.raises(ValueError, match="initial_rate must be between 0 and 1"):
            GuytonKlingerStrategy(initial_rate=0)

        with pytest.raises(ValueError, match="initial_rate must be between 0 and 1"):
            GuytonKlingerStrategy(initial_rate=1.5)

        # Invalid guard_pct
        with pytest.raises(ValueError, match="guard_pct must be between 0 and 1"):
            GuytonKlingerStrategy(guard_pct=0)

        with pytest.raises(ValueError, match="guard_pct must be between 0 and 1"):
            GuytonKlingerStrategy(guard_pct=1.5)

        # Invalid raise_pct
        with pytest.raises(ValueError, match="raise_pct must be between 0 and 1"):
            GuytonKlingerStrategy(raise_pct=0)

        # Invalid cut_pct
        with pytest.raises(ValueError, match="cut_pct must be between 0 and 1"):
            GuytonKlingerStrategy(cut_pct=1.5)

    def test_first_year_withdrawal(self):
        """Test withdrawal calculation for the first year."""
        strategy = GuytonKlingerStrategy(initial_rate=0.05)
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # First call should return initial rate * balance
        withdrawal = strategy.calculate_withdrawal(None, params)
        assert withdrawal == 50_000  # 5% of $1,000,000

    def test_withdrawal_with_state(self):
        """Test withdrawal calculation with year state."""
        strategy = GuytonKlingerStrategy(initial_rate=0.05)
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize base withdrawal
        strategy.calculate_withdrawal(None, params)

        # Create state for second year
        state = YearState(
            year=2025,
            age=65,
            balance=1_050_000,
            inflation=0.03,
            withdrawal_nominal=None,
        )

        withdrawal = strategy.calculate_withdrawal(state, params)
        # Should be base withdrawal adjusted for inflation: 50,000 * 1.03
        assert withdrawal == pytest.approx(51_500)

    def test_upper_guardrail_adjustment(self):
        """Test withdrawal reduction when hitting upper guardrail."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.05, guard_pct=0.20, cut_pct=0.10  # ±20% guardrails
        )
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Simulate market crash - portfolio drops to 750,000
        # Current rate would be 50,000 / 750,000 = 0.0667 > 0.06 (upper guardrail)
        state = YearState(
            year=2025, age=65, balance=750_000, inflation=0.02, withdrawal_nominal=None
        )

        withdrawal = strategy.calculate_withdrawal(state, params)
        # Expected: 50,000 * 1.02 (inflation) * 0.9 (10% cut) = 45,900
        assert withdrawal == pytest.approx(45_900)

    def test_lower_guardrail_adjustment(self):
        """Test withdrawal increase when hitting lower guardrail."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.05, guard_pct=0.20, raise_pct=0.10  # ±20% guardrails
        )
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Simulate strong market - portfolio grows to 1,500,000
        # Current rate would be 50,000 / 1,500,000 = 0.0333 < 0.04 (lower guardrail)
        state = YearState(
            year=2025,
            age=65,
            balance=1_500_000,
            inflation=0.02,
            withdrawal_nominal=None,
        )

        withdrawal = strategy.calculate_withdrawal(state, params)
        # Expected: 50,000 * 1.02 (inflation) * 1.1 (10% raise) = 56,100
        assert withdrawal == pytest.approx(56_100)

    def test_prosperity_rule(self):
        """Test that no cuts are made when portfolio > 120% of initial."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.05, guard_pct=0.20, cut_pct=0.10
        )
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Portfolio is 130% of initial but withdrawal rate exceeds upper guardrail
        # Rate = 50,000 / 800,000 = 0.0625 > 0.06, but portfolio is 1.3M (> 1.2M)
        state = YearState(
            year=2025,
            age=65,
            balance=1_300_000,
            inflation=0.02,
            withdrawal_nominal=None,
        )

        # Need to set up a scenario where rate > upper guardrail but balance > 120%
        # This requires a high withdrawal relative to balance
        # Let's increase the base withdrawal first
        strategy._base_withdrawal = 80_000  # Force high withdrawal

        withdrawal = strategy.calculate_withdrawal(state, params)
        # Should only adjust for inflation, no cut: 80,000 * 1.02
        assert withdrawal == pytest.approx(81_600)

    def test_capital_preservation_rule(self):
        """Test that no raises are made when portfolio < 80% of initial."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.05, guard_pct=0.20, raise_pct=0.10
        )
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Portfolio is 70% of initial but withdrawal rate below lower guardrail
        state = YearState(
            year=2025, age=65, balance=700_000, inflation=0.02, withdrawal_nominal=None
        )

        # Force low withdrawal to trigger lower guardrail
        strategy._base_withdrawal = 20_000

        withdrawal = strategy.calculate_withdrawal(state, params)
        # Should only adjust for inflation, no raise: 20,000 * 1.02
        assert withdrawal == pytest.approx(20_400)

    def test_cumulative_inflation_tracking(self):
        """Test that cumulative inflation is tracked correctly."""
        strategy = GuytonKlingerStrategy(initial_rate=0.05)
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Year 1: 2% inflation
        state1 = YearState(
            year=2025,
            age=65,
            balance=1_000_000,
            inflation=0.02,
            withdrawal_nominal=None,
        )
        withdrawal1 = strategy.calculate_withdrawal(state1, params)
        assert withdrawal1 == pytest.approx(51_000)  # 50,000 * 1.02

        # Year 2: 3% inflation
        state2 = YearState(
            year=2026,
            age=66,
            balance=1_000_000,
            inflation=0.03,
            withdrawal_nominal=None,
        )
        withdrawal2 = strategy.calculate_withdrawal(state2, params)
        assert withdrawal2 == pytest.approx(52_530)  # 50,000 * 1.02 * 1.03

        # Year 3: 1% inflation
        state3 = YearState(
            year=2027,
            age=67,
            balance=1_000_000,
            inflation=0.01,
            withdrawal_nominal=None,
        )
        withdrawal3 = strategy.calculate_withdrawal(state3, params)
        assert withdrawal3 == pytest.approx(53_055.3)  # 50,000 * 1.02 * 1.03 * 1.01

    def test_zero_balance_handling(self):
        """Test handling of zero portfolio balance."""
        strategy = GuytonKlingerStrategy(initial_rate=0.05)
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        state = YearState(
            year=2025, age=65, balance=0, inflation=0.02, withdrawal_nominal=None
        )

        # Should return 0 when balance is 0
        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 0.0

    def test_repr(self):
        """Test string representation."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.04, guard_pct=0.25, raise_pct=0.15, cut_pct=0.08
        )

        repr_str = repr(strategy)
        assert "GuytonKlingerStrategy" in repr_str
        assert "initial_rate=0.04" in repr_str
        assert "guard_pct=0.25" in repr_str
        assert "raise_pct=0.15" in repr_str
        assert "cut_pct=0.08" in repr_str

    def test_scenario_market_crash_triggers_cut(self):
        """Test scenario where market crash triggers a cut."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.05, guard_pct=0.20, cut_pct=0.10
        )
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Year 1: Normal
        state1 = YearState(
            year=2025,
            age=65,
            balance=1_000_000,
            inflation=0.02,
            withdrawal_nominal=None,
        )
        withdrawal1 = strategy.calculate_withdrawal(state1, params)
        assert withdrawal1 == pytest.approx(51_000)

        # Year 2: Market crash, portfolio drops significantly
        state2 = YearState(
            year=2026, age=66, balance=700_000, inflation=0.02, withdrawal_nominal=None
        )
        withdrawal2 = strategy.calculate_withdrawal(state2, params)

        # Check if cut was applied
        # Previous base was 50,000, with cumulative inflation of 1.02 * 1.02 = 1.0404
        # Rate = 51,000 * 1.02 / 700,000 = 0.0743 > 0.06 (upper guardrail)
        # Should apply 10% cut
        expected = 51_000 * 1.02 * 0.9
        assert withdrawal2 == pytest.approx(expected)

    def test_scenario_strong_market_triggers_raise(self):
        """Test scenario where strong market triggers a raise."""
        strategy = GuytonKlingerStrategy(
            initial_rate=0.05, guard_pct=0.20, raise_pct=0.10
        )
        params = PortfolioParams(init_balance=1_000_000, equity_pct=0.6, fees_bps=30)

        # Initialize
        strategy.calculate_withdrawal(None, params)

        # Year 1: Strong market growth
        state1 = YearState(
            year=2025,
            age=65,
            balance=1_400_000,
            inflation=0.02,
            withdrawal_nominal=None,
        )
        withdrawal1 = strategy.calculate_withdrawal(state1, params)

        # Rate = 50,000 * 1.02 / 1,400,000 = 0.0364 < 0.04 (lower guardrail)
        # Should apply 10% raise
        expected = 50_000 * 1.02 * 1.1
        assert withdrawal1 == pytest.approx(expected)
