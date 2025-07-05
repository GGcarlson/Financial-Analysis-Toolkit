#!/usr/bin/env python3
"""
Performance benchmark for vectorized simulation optimization.

This script measures the performance improvement from using lightweight 
dataclass instead of Pydantic objects in the hot path.
"""

import time
from pathlib import Path
import sys

# Add src to path so we can import capstone_finance
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from capstone_finance.core.ledger import run_simulation_vectorized
from capstone_finance.core.market import MarketSimulator
from capstone_finance.core.models import PortfolioParams
from capstone_finance.strategies.dummy import DummyStrategy


def benchmark_vectorized_simulation():
    """Benchmark the vectorized simulation performance."""
    print("🚀 Benchmarking Vectorized Simulation Performance")
    print("=" * 60)
    
    # Test parameters
    params = PortfolioParams(
        init_balance=1_000_000,
        equity_pct=0.6, 
        fees_bps=50,
        seed=42
    )
    
    simulator = MarketSimulator(params, mode="lognormal")
    strategy = DummyStrategy()
    
    # Small test (baseline)
    print("Small test (1,000 paths x 30 years):")
    start_time = time.time()
    result_small = run_simulation_vectorized(
        simulator, strategy, params, years=30, paths=1000
    )
    small_time = time.time() - start_time
    print(f"  Time: {small_time:.3f}s")
    print(f"  Result shape: {result_small.shape}")
    
    # Medium test
    print("\nMedium test (5,000 paths x 40 years):")
    start_time = time.time()
    result_medium = run_simulation_vectorized(
        simulator, strategy, params, years=40, paths=5000
    )
    medium_time = time.time() - start_time
    print(f"  Time: {medium_time:.3f}s")
    print(f"  Result shape: {result_medium.shape}")
    
    # Large test (target performance requirement)
    print("\nLarge test (10,000 paths x 40 years):")
    start_time = time.time()
    result_large = run_simulation_vectorized(
        simulator, strategy, params, years=40, paths=10000
    )
    large_time = time.time() - start_time
    print(f"  Time: {large_time:.3f}s")
    print(f"  Result shape: {result_large.shape}")
    
    # Performance analysis
    print("\n📊 Performance Analysis:")
    print("-" * 30)
    paths_per_sec_small = 1000 / small_time
    paths_per_sec_medium = 5000 / medium_time
    paths_per_sec_large = 10000 / large_time
    
    print(f"Small test throughput:  {paths_per_sec_small:,.0f} paths/second")
    print(f"Medium test throughput: {paths_per_sec_medium:,.0f} paths/second")
    print(f"Large test throughput:  {paths_per_sec_large:,.0f} paths/second")
    
    # Check target performance (should be < 2.5s for large test)
    target_time = 2.5
    if large_time <= target_time:
        print(f"\n✅ PASS: Large test completed in {large_time:.3f}s (target: <{target_time}s)")
    else:
        print(f"\n❌ FAIL: Large test took {large_time:.3f}s (target: <{target_time}s)")
    
    print(f"\n🎯 Performance Summary:")
    print(f"  - Lightweight dataclass optimization is active")
    print(f"  - Peak throughput: {max(paths_per_sec_small, paths_per_sec_medium, paths_per_sec_large):,.0f} paths/second")
    print(f"  - Memory efficiency: Using dataclass(slots=True) for minimal overhead")


if __name__ == "__main__":
    benchmark_vectorized_simulation()