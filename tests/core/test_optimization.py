"""Tests for performance optimizations."""

import time
import numpy as np
import pytest

from capstone_finance.core.ledger import run_simulation_vectorized, CashFlowLedger, _State
from capstone_finance.core.market import MarketSimulator
from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.strategies.dummy import DummyStrategy
from capstone_finance.strategies.base import BaseStrategy


class StateCompatibilityStrategy(BaseStrategy):
    """Test strategy that works with both YearState and _State objects."""
    
    def calculate_withdrawal(self, state, params):
        """Calculate withdrawal that works with both state types."""
        if state is None:
            return 0.0
        
        # Should work with both YearState and _State
        balance = state.balance
        age = state.age
        
        # Simple age-based withdrawal for testing
        return balance * (age - 64) * 0.001  # 0.1% per year over age 65


class TestPerformanceOptimization:
    """Tests for the _State dataclass optimization."""

    def test_state_dataclass_creation(self):
        """Test that _State dataclass can be created and accessed."""
        state = _State(
            year=2024,
            age=65,
            balance=1_000_000.0,
            inflation=0.03,
            withdrawal_nominal=40_000.0
        )
        
        assert state.year == 2024
        assert state.age == 65
        assert state.balance == 1_000_000.0
        assert state.inflation == 0.03
        assert state.withdrawal_nominal == 40_000.0

    def test_state_compatibility_with_strategies(self):
        """Test that strategies work with both YearState and _State."""
        strategy = StateCompatibilityStrategy()
        params = PortfolioParams(
            init_balance=1_000_000,
            equity_pct=0.6,
            fees_bps=50,
            seed=42
        )
        
        # Test with YearState (Pydantic)
        year_state = YearState(
            year=2024,
            age=70,
            balance=1_000_000.0,
            inflation=0.03,
            withdrawal_nominal=None
        )
        withdrawal_pydantic = strategy.calculate_withdrawal(year_state, params)
        
        # Test with _State (dataclass)
        light_state = _State(
            year=2024,
            age=70,
            balance=1_000_000.0,
            inflation=0.03,
            withdrawal_nominal=None
        )
        withdrawal_dataclass = strategy.calculate_withdrawal(light_state, params)
        
        # Should get identical results
        assert withdrawal_pydantic == withdrawal_dataclass
        assert withdrawal_pydantic == 1_000_000.0 * (70 - 64) * 0.001  # 6.0

    def test_vectorized_performance_benchmark(self):
        """Test that vectorized simulation meets performance requirements."""
        params = PortfolioParams(
            init_balance=1_000_000,
            equity_pct=0.6,
            fees_bps=50,
            seed=42
        )
        simulator = MarketSimulator(params, mode="lognormal")
        strategy = DummyStrategy()
        
        # Benchmark test: 10,000 paths x 40 years should complete in < 2.5 seconds
        start_time = time.time()
        result = run_simulation_vectorized(
            simulator, strategy, params, years=40, paths=10000
        )
        elapsed_time = time.time() - start_time
        
        # Assertions
        assert result.shape == (10000, 40)
        assert elapsed_time < 2.5, f"Performance target missed: {elapsed_time:.3f}s > 2.5s"
        
        # Verify results are reasonable
        assert np.all(result >= 0)  # No negative balances
        assert np.all(np.isfinite(result))  # No NaN or infinite values

    def test_strategy_compatibility_regression(self):
        """Test that existing strategies still work after optimization."""
        params = PortfolioParams(
            init_balance=1_000_000,
            equity_pct=0.6,
            fees_bps=50,
            seed=42
        )
        
        # Use a simple fixed return simulator for deterministic comparison
        class FixedReturnSimulator:
            def __init__(self, fixed_return=0.05):
                self.fixed_return = fixed_return
            
            def generate(self, n_paths, n_years):
                import numpy as np
                return np.full((n_paths, n_years), self.fixed_return, dtype=np.float64)
        
        simulator = FixedReturnSimulator(0.05)  # 5% fixed return
        strategy = DummyStrategy()
        
        # Run both regular and vectorized simulations with deterministic returns
        ledger = CashFlowLedger(simulator, strategy, params)
        regular_results = ledger.run(years=5, paths=10)
        
        vectorized_results = run_simulation_vectorized(
            simulator, strategy, params, years=5, paths=10
        )
        
        # Compare final balances (should be identical with fixed returns)
        for path_idx in range(10):
            for year_idx in range(5):
                regular_balance = regular_results[path_idx][year_idx].balance
                vectorized_balance = vectorized_results[path_idx, year_idx]
                assert abs(regular_balance - vectorized_balance) < 0.01, \
                    f"Balance mismatch at path {path_idx}, year {year_idx}: " \
                    f"regular={regular_balance}, vectorized={vectorized_balance}"

    @pytest.mark.performance
    def test_memory_efficiency(self):
        """Test that _State uses less memory than YearState."""
        import sys
        
        # Create instances
        year_state = YearState(
            year=2024,
            age=65,
            balance=1_000_000.0,
            inflation=0.03,
            withdrawal_nominal=None
        )
        
        light_state = _State(
            year=2024,
            age=65,
            balance=1_000_000.0,
            inflation=0.03,
            withdrawal_nominal=None
        )
        
        # Measure memory usage (rough comparison)
        pydantic_size = sys.getsizeof(year_state)
        dataclass_size = sys.getsizeof(light_state)
        
        # _State should be more memory efficient
        print(f"YearState size: {pydantic_size} bytes")
        print(f"_State size: {dataclass_size} bytes")
        print(f"Memory reduction: {((pydantic_size - dataclass_size) / pydantic_size * 100):.1f}%")
        
        # Dataclass with slots should be smaller
        assert dataclass_size <= pydantic_size