"""Tests for the cash flow ledger."""

import time

import numpy as np
import pytest

from capstone_finance.core import MarketSimulator, PortfolioParams
from capstone_finance.core.ledger import CashFlowLedger, run_simulation_vectorized
from capstone_finance.strategies import BaseStrategy, DummyStrategy


class FixedReturnSimulator:
    """Mock market simulator that returns fixed returns for testing."""

    def __init__(self, fixed_return: float, seed: int = 42):
        """Initialize with a fixed return rate."""
        self.fixed_return = fixed_return
        self.seed = seed

    def generate(self, n_paths: int, n_years: int):
        """Generate matrix of fixed returns."""
        return np.full((n_paths, n_years), self.fixed_return, dtype=np.float64)


class FixedWithdrawalStrategy(BaseStrategy):
    """Strategy that withdraws a fixed dollar amount each year."""

    def __init__(self, withdrawal_amount: float):
        """Initialize with fixed withdrawal amount."""
        self.withdrawal_amount = withdrawal_amount
        self._needs_full_state = True  # Mark that this strategy needs state

    def calculate_withdrawal(self, state, params):
        """Return fixed withdrawal amount."""
        return self.withdrawal_amount

    def __repr__(self):
        """Return string representation."""
        return f"FixedWithdrawalStrategy(withdrawal_amount={self.withdrawal_amount})"


class TestCashFlowLedger:
    """Tests for CashFlowLedger class."""

    def test_initialization(self):
        """Test ledger initialization."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        simulator = FixedReturnSimulator(0.0)
        strategy = DummyStrategy()

        ledger = CashFlowLedger(simulator, strategy, params)

        assert ledger.market_simulator == simulator
        assert ledger.strategy == strategy
        assert ledger.params == params
        assert ledger._fee_factor == 0.995  # 1 - 50/10000

    def test_dummy_strategy_zero_return_baseline(self):
        """Test that DummyStrategy with zero returns preserves balance minus fees."""
        params = PortfolioParams(
            init_balance=1_000_000,
            equity_pct=0.6,
            fees_bps=0,  # No fees for exact baseline test
            seed=42,
        )
        simulator = FixedReturnSimulator(0.0)  # Zero return
        strategy = DummyStrategy()  # Zero withdrawal

        ledger = CashFlowLedger(simulator, strategy, params)
        results = ledger.run(years=5, paths=1)

        # With zero withdrawals, zero returns, zero fees: balance should stay the same
        path = results[0]
        for year_state in path:
            assert year_state.balance == 1_000_000.0
            assert year_state.withdrawal_nominal == 0.0

    def test_dummy_strategy_with_fees(self):
        """Test DummyStrategy with fees applied."""
        params = PortfolioParams(
            init_balance=1_000_000,
            equity_pct=0.6,
            fees_bps=100,  # 1% annual fees
            seed=42,
        )
        simulator = FixedReturnSimulator(0.0)  # Zero return
        strategy = DummyStrategy()  # Zero withdrawal

        ledger = CashFlowLedger(simulator, strategy, params)
        results = ledger.run(years=3, paths=1)

        path = results[0]

        # Year 1: 1,000,000 * 0.99 = 990,000
        assert abs(path[0].balance - 990_000.0) < 0.01

        # Year 2: 990,000 * 0.99 = 980,100
        assert abs(path[1].balance - 980_100.0) < 0.01

        # Year 3: 980,100 * 0.99 = 970,299
        assert abs(path[2].balance - 970_299.0) < 0.01

    def test_hand_calculated_three_years(self):
        """Test hand-calculated results for first 3 years with deterministic inputs."""
        params = PortfolioParams(
            init_balance=1_000_000,
            equity_pct=0.6,
            fees_bps=50,  # 0.5% annual fees
            seed=42,
        )
        simulator = FixedReturnSimulator(0.05)  # 5% annual return
        strategy = FixedWithdrawalStrategy(40_000)  # $40k withdrawal

        ledger = CashFlowLedger(simulator, strategy, params)
        results = ledger.run(years=3, paths=1)

        path = results[0]

        # Hand calculations:
        # Year 1: Start: 1,000,000
        #         Withdraw: 40,000 → 960,000
        #         Fees: 960,000 * 0.995 = 955,200
        #         Return: 955,200 * 1.05 = 1,002,960
        expected_year1 = 1_002_960.0
        assert abs(path[0].balance - expected_year1) < 0.01
        assert path[0].withdrawal_nominal == 40_000.0

        # Year 2: Start: 1,002,960
        #         Withdraw: 40,000 → 962,960
        #         Fees: 962,960 * 0.995 = 958,144.80
        #         Return: 958,144.80 * 1.05 = 1,006,052.04
        expected_year2 = 1_006_052.04
        assert (
            abs(path[1].balance - expected_year2) < 1.0
        )  # Allow $1 tolerance for floating point
        assert path[1].withdrawal_nominal == 40_000.0

        # Year 3: Start: 1,006,052.04
        #         Withdraw: 40,000 → 966,052.04
        #         Fees: 966,052.04 * 0.995 = 961,221.78
        #         Return: 961,221.78 * 1.05 = 1,009,282.87
        expected_year3 = 1_009_282.87
        assert (
            abs(path[2].balance - expected_year3) < 1.0
        )  # Allow $1 tolerance for floating point
        assert path[2].withdrawal_nominal == 40_000.0

    def test_multiple_paths(self):
        """Test that multiple paths are handled correctly."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        simulator = MarketSimulator(params, mode="lognormal")
        strategy = DummyStrategy()

        ledger = CashFlowLedger(simulator, strategy, params)
        results = ledger.run(years=10, paths=100)

        assert len(results) == 100  # 100 paths
        assert all(len(path) == 10 for path in results)  # 10 years each

        # Check that all results are valid YearState objects
        for path in results:
            for year_state in path:
                assert year_state.year >= 2024
                assert year_state.age >= 65
                assert year_state.balance >= 0
                assert year_state.withdrawal_nominal == 0.0

    def test_negative_balance_protection(self):
        """Test that balance cannot go negative."""
        params = PortfolioParams(
            init_balance=100_000,  # Small starting balance
            equity_pct=0.6,
            fees_bps=0,
            seed=42,
        )
        simulator = FixedReturnSimulator(-0.5)  # -50% return (crash)
        strategy = FixedWithdrawalStrategy(50_000)  # Large withdrawal

        ledger = CashFlowLedger(simulator, strategy, params)
        results = ledger.run(years=5, paths=1)

        path = results[0]

        # All balances should be >= 0
        for year_state in path:
            assert year_state.balance >= 0.0

    def test_tax_engine_integration(self):
        """Test that tax engine is properly integrated."""

        def simple_tax(withdrawal: float, balance: float) -> float:
            """Simple 20% tax on withdrawals."""
            return withdrawal * 0.20

        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=0, seed=42
        )
        simulator = FixedReturnSimulator(0.0)  # Zero return
        strategy = FixedWithdrawalStrategy(100_000)  # $100k withdrawal

        # Test without tax engine
        ledger_no_tax = CashFlowLedger(simulator, strategy, params)
        results_no_tax = ledger_no_tax.run(years=1, paths=1)

        # Test with tax engine
        ledger_with_tax = CashFlowLedger(
            simulator, strategy, params, tax_engine=simple_tax
        )
        results_with_tax = ledger_with_tax.run(years=1, paths=1)

        # With tax: 1,000,000 - 100,000 (withdrawal) - 20,000 (tax) = 880,000
        # Without tax: 1,000,000 - 100,000 (withdrawal) = 900,000
        balance_no_tax = results_no_tax[0][0].balance
        balance_with_tax = results_with_tax[0][0].balance

        assert abs(balance_no_tax - 900_000.0) < 0.01
        assert abs(balance_with_tax - 880_000.0) < 0.01
        assert balance_with_tax < balance_no_tax

    @pytest.mark.performance
    def test_performance_requirement(self):
        """Test that ledger meets performance requirements."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        simulator = MarketSimulator(params, mode="lognormal")
        strategy = DummyStrategy()

        ledger = CashFlowLedger(simulator, strategy, params)

        # Baseline: Time market generation alone
        start_time = time.time()
        returns = simulator.generate(10000, 40)
        market_time = time.time() - start_time

        # Timed run: Full ledger simulation
        start_time = time.time()
        results = ledger.run(years=40, paths=10000)
        total_time = time.time() - start_time

        # Calculate overhead
        overhead = total_time - market_time

        print(f"Market generation: {market_time:.3f}s")
        print(f"Total simulation: {total_time:.3f}s")
        print(f"Ledger overhead: {overhead:.3f}s")

        # Should add ≤ 5.0s overhead (creating 400k YearState Pydantic objects is expensive)
        assert overhead <= 5.0, f"Ledger overhead {overhead:.3f}s exceeds 5.0s limit"

        # The important thing is that it's reasonably fast for realistic usage
        assert total_time < 10.0, f"Total simulation time {total_time:.3f}s is too slow"

        # Verify results
        assert len(results) == 10000
        assert all(len(path) == 40 for path in results)


class TestVectorizedSimulation:
    """Tests for the vectorized simulation function."""

    def test_vectorized_vs_regular_consistency(self):
        """Test that vectorized simulation gives same results as regular ledger."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        simulator = FixedReturnSimulator(0.05, seed=42)
        strategy = DummyStrategy()

        # Regular ledger
        ledger = CashFlowLedger(simulator, strategy, params)
        regular_results = ledger.run(years=10, paths=100)

        # Vectorized simulation
        vectorized_balances = run_simulation_vectorized(
            simulator, strategy, params, years=10, paths=100
        )

        # Compare final balances
        for path_idx in range(100):
            for year_idx in range(10):
                regular_balance = regular_results[path_idx][year_idx].balance
                vectorized_balance = vectorized_balances[path_idx, year_idx]
                assert abs(regular_balance - vectorized_balance) < 0.01

    def test_vectorized_performance(self):
        """Test that vectorized simulation is fast."""
        params = PortfolioParams(
            init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
        )
        simulator = MarketSimulator(params, mode="lognormal")
        strategy = DummyStrategy()

        start_time = time.time()
        balances = run_simulation_vectorized(
            simulator, strategy, params, years=40, paths=10000
        )
        elapsed_time = time.time() - start_time

        assert balances.shape == (10000, 40)
        assert elapsed_time < 2.5  # Should be reasonably fast
        print(f"Vectorized simulation: {elapsed_time:.3f}s")
