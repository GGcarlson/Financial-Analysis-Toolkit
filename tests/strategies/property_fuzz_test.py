"""Property-based testing for withdrawal strategies using Hypothesis.

This module validates that all withdrawal strategies satisfy common financial
properties using fuzz testing with Hypothesis.
"""

import importlib.metadata
import math
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.strategies.base import BaseStrategy


def get_available_strategies() -> dict[str, type[BaseStrategy]]:
    """Discover available strategies from entry-points."""
    strategies = {}
    try:
        eps = importlib.metadata.entry_points(group="capstone_finance.strategies")
        for ep in eps:
            try:
                strategy_cls = ep.load()
                strategies[ep.name] = strategy_cls
            except Exception:
                # Skip strategies that fail to load
                continue
    except Exception:
        # If entry points discovery fails, return empty dict
        pass

    return strategies


# Hypothesis strategies for generating test data
@st.composite
def year_state_strategy(draw: Any) -> YearState:
    """Generate valid YearState instances."""
    return YearState(
        year=draw(st.integers(min_value=2024, max_value=2100)),
        age=draw(st.integers(min_value=18, max_value=120)),
        balance=draw(st.floats(min_value=0.0, max_value=10_000_000.0)),
        inflation=draw(st.floats(min_value=-0.1, max_value=0.2)),  # -10% to 20%
        withdrawal_nominal=draw(
            st.one_of(st.none(), st.floats(min_value=0.0, max_value=1_000_000.0))
        ),
    )


@st.composite
def portfolio_params_strategy(draw: Any) -> PortfolioParams:
    """Generate valid PortfolioParams instances."""
    return PortfolioParams(
        init_balance=draw(st.floats(min_value=1.0, max_value=50_000_000.0)),
        equity_pct=draw(st.floats(min_value=0.0, max_value=1.0)),
        fees_bps=draw(st.integers(min_value=0, max_value=500)),  # 0 to 5%
        seed=draw(st.integers(min_value=0, max_value=2**31 - 1)),
    )


# Get all available strategies for parameterization
AVAILABLE_STRATEGIES = get_available_strategies()
STRATEGY_NAMES = list(AVAILABLE_STRATEGIES.keys())


class TestStrategyProperties:
    """Property-based tests for withdrawal strategies."""

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    @given(
        params=portfolio_params_strategy(),
        state=st.one_of(st.none(), year_state_strategy()),
    )
    @settings(max_examples=1000, deadline=30000)  # 1000 examples, 30s timeout
    def test_withdrawal_never_nan(
        self, strategy_name: str, params: PortfolioParams, state: YearState | None
    ) -> None:
        """Test that withdrawal calculations never return NaN."""
        strategy = AVAILABLE_STRATEGIES[strategy_name]()
        withdrawal = strategy.calculate_withdrawal(state, params)

        assert not math.isnan(withdrawal), f"Strategy {strategy_name} returned NaN"
        assert math.isfinite(
            withdrawal
        ), f"Strategy {strategy_name} returned infinite value"

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    @given(
        params=portfolio_params_strategy(),
        state=st.one_of(st.none(), year_state_strategy()),
    )
    @settings(max_examples=1000, deadline=30000)
    def test_withdrawal_non_negative(
        self, strategy_name: str, params: PortfolioParams, state: YearState | None
    ) -> None:
        """Test that withdrawal amounts are always non-negative."""
        strategy = AVAILABLE_STRATEGIES[strategy_name]()
        withdrawal = strategy.calculate_withdrawal(state, params)

        assert (
            withdrawal >= 0.0
        ), f"Strategy {strategy_name} returned negative withdrawal: {withdrawal}"

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    @given(params=portfolio_params_strategy(), state=year_state_strategy())
    @settings(max_examples=1000, deadline=30000)
    def test_inflation_monotonicity(
        self, strategy_name: str, params: PortfolioParams, state: YearState
    ) -> None:
        """Test that higher inflation leads to higher or equal withdrawal amounts.
        
        Note: Guyton-Klinger strategy is excluded because its guardrail logic
        can intentionally reduce withdrawals to preserve capital, violating
        strict inflation monotonicity.
        """
        # Skip Guyton-Klinger as it violates monotonicity by design
        if strategy_name == "guyton_klinger":
            return
        
        # Create fresh strategy instances to avoid state contamination
        strategy_low = AVAILABLE_STRATEGIES[strategy_name]()
        strategy_high = AVAILABLE_STRATEGIES[strategy_name]()

        # Test with original inflation
        withdrawal_low = strategy_low.calculate_withdrawal(state, params)

        # Test with higher inflation (add 1%)
        state_high_inflation = YearState(
            year=state.year,
            age=state.age,
            balance=state.balance,
            inflation=state.inflation + 0.01,
            withdrawal_nominal=state.withdrawal_nominal,
        )
        withdrawal_high = strategy_high.calculate_withdrawal(state_high_inflation, params)

        # For inflation-adjusted strategies, higher inflation should result in
        # higher or equal withdrawal amounts
        assert withdrawal_high >= withdrawal_low, (
            f"Strategy {strategy_name} violated inflation monotonicity: "
            f"low_inflation={state.inflation:.3f} -> {withdrawal_low:.2f}, "
            f"high_inflation={state_high_inflation.inflation:.3f} -> {withdrawal_high:.2f}"
        )

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    @given(
        params=portfolio_params_strategy(),
        state=st.one_of(st.none(), year_state_strategy()),
    )
    @settings(max_examples=1000, deadline=30000)
    def test_deterministic_behavior(
        self, strategy_name: str, params: PortfolioParams, state: YearState | None
    ) -> None:
        """Test that same inputs always produce same outputs."""
        strategy1 = AVAILABLE_STRATEGIES[strategy_name]()
        strategy2 = AVAILABLE_STRATEGIES[strategy_name]()

        withdrawal1 = strategy1.calculate_withdrawal(state, params)
        withdrawal2 = strategy2.calculate_withdrawal(state, params)

        assert withdrawal1 == withdrawal2, (
            f"Strategy {strategy_name} is not deterministic: "
            f"got {withdrawal1} and {withdrawal2} for same inputs"
        )

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    @given(params=portfolio_params_strategy(), state=year_state_strategy())
    @settings(max_examples=1000, deadline=30000)
    def test_withdrawal_reasonable_bounds(
        self, strategy_name: str, params: PortfolioParams, state: YearState
    ) -> None:
        """Test that withdrawal amounts are within reasonable bounds."""
        strategy = AVAILABLE_STRATEGIES[strategy_name]()
        withdrawal = strategy.calculate_withdrawal(state, params)

        # For strategies that depend on current balance (like constant_pct, endowment),
        # use current balance as the bound. For others, use initial balance.
        if strategy_name in ["constant_pct", "endowment"]:
            # These strategies can withdraw up to 100% of current balance
            max_reasonable = state.balance * 1.0
        else:
            # Other strategies should not exceed 100% of initial balance per year
            # (this is a very generous upper bound to catch obvious errors)
            max_reasonable = params.init_balance * 1.0

        assert withdrawal <= max_reasonable, (
            f"Strategy {strategy_name} returned unreasonably high withdrawal: "
            f"{withdrawal:.2f} > {max_reasonable:.2f} (100% of bound)"
        )

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    @given(params=portfolio_params_strategy())
    @settings(max_examples=1000, deadline=30000)
    def test_none_state_handling(
        self, strategy_name: str, params: PortfolioParams
    ) -> None:
        """Test that strategies handle None state gracefully."""
        strategy = AVAILABLE_STRATEGIES[strategy_name]()

        # Should not raise an exception when state is None
        try:
            withdrawal = strategy.calculate_withdrawal(None, params)
            assert isinstance(
                withdrawal, int | float
            ), f"Strategy {strategy_name} did not return a number when state is None"
            assert not math.isnan(
                withdrawal
            ), f"Strategy {strategy_name} returned NaN when state is None"
        except Exception as e:
            pytest.fail(
                f"Strategy {strategy_name} raised exception with None state: {e}"
            )


def test_strategies_discovered():
    """Test that at least some strategies are discovered via entry points."""
    strategies = get_available_strategies()
    assert len(strategies) > 0, "No strategies discovered via entry points"

    # Check that we have the expected built-in strategies
    expected_strategies = {"dummy", "four_percent_rule"}
    discovered_names = set(strategies.keys())

    assert expected_strategies.issubset(discovered_names), (
        f"Expected strategies {expected_strategies} not all discovered. "
        f"Found: {discovered_names}"
    )


def test_all_strategies_inherit_from_base():
    """Test that all discovered strategies inherit from BaseStrategy."""
    strategies = get_available_strategies()

    for name, strategy_cls in strategies.items():
        assert issubclass(
            strategy_cls, BaseStrategy
        ), f"Strategy {name} does not inherit from BaseStrategy"

        # Check that the strategy implements the required method
        assert hasattr(
            strategy_cls, "calculate_withdrawal"
        ), f"Strategy {name} does not have calculate_withdrawal method"
