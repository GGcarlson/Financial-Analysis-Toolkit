#!/usr/bin/env python3
"""Benchmark script for market simulator performance and statistics.

Tests both log-normal and bootstrap modes with 10,000 paths × 40 years.
"""

import sys
import time
from pathlib import Path

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capstone_finance.core import PortfolioParams
from src.capstone_finance.core.market import MarketSimulator


def benchmark_mode(mode: str, n_paths: int = 10000, n_years: int = 40):
    """Benchmark a specific simulation mode.

    Args:
        mode: 'lognormal' or 'bootstrap'
        n_paths: Number of simulation paths
        n_years: Number of years to simulate

    Returns:
        Tuple of (elapsed_time, mean_return, std_return)
    """
    print(f"\nBenchmarking {mode} mode...")
    print(f"Generating {n_paths:,} paths × {n_years} years")

    # Create simulator
    params = PortfolioParams(
        init_balance=1_000_000, equity_pct=0.6, fees_bps=50, seed=42
    )
    sim = MarketSimulator(params, mode=mode)

    # Warm-up run (to ensure any one-time initialization is done)
    print("Warm-up run...")
    sim.generate(100, 10)

    # Timed run
    print("Timed run...")
    start_time = time.time()
    returns = sim.generate(n_paths, n_years)
    elapsed_time = time.time() - start_time

    # Calculate statistics
    mean_return = np.mean(returns)
    std_return = np.std(returns)

    # Additional statistics
    median_return = np.median(returns)
    min_return = np.min(returns)
    max_return = np.max(returns)
    percentile_5 = np.percentile(returns, 5)
    percentile_95 = np.percentile(returns, 95)

    # Print results
    print(f"\nResults for {mode} mode:")
    print(f"  Runtime: {elapsed_time:.3f} seconds")
    print(f"  Mean return: {mean_return:.4f} ({mean_return*100:.2f}%)")
    print(f"  Std deviation: {std_return:.4f} ({std_return*100:.2f}%)")
    print(f"  Median return: {median_return:.4f} ({median_return*100:.2f}%)")
    print(f"  Min return: {min_return:.4f} ({min_return*100:.2f}%)")
    print(f"  Max return: {max_return:.4f} ({max_return*100:.2f}%)")
    print(f"  5th percentile: {percentile_5:.4f} ({percentile_5*100:.2f}%)")
    print(f"  95th percentile: {percentile_95:.4f} ({percentile_95*100:.2f}%)")

    # Performance check
    if elapsed_time > 2.0:
        print("  ⚠️  WARNING: Runtime exceeds 2 second target!")
    else:
        print("  ✓ Performance target met (< 2 seconds)")

    return elapsed_time, mean_return, std_return


def main():
    """Run benchmarks for both simulation modes."""
    print("=" * 60)
    print("Market Simulator Benchmark")
    print("=" * 60)

    # Test parameters
    n_paths = 10000
    n_years = 40

    print("\nBenchmark configuration:")
    print(f"  Paths: {n_paths:,}")
    print(f"  Years: {n_years}")
    print(f"  Total returns: {n_paths * n_years:,}")

    # Benchmark both modes
    results = {}
    for mode in ["lognormal", "bootstrap"]:
        elapsed, mean_ret, std_ret = benchmark_mode(mode, n_paths, n_years)
        results[mode] = {"runtime": elapsed, "mean": mean_ret, "std": std_ret}

    # Summary comparison
    print("\n" + "=" * 60)
    print("Summary Comparison")
    print("=" * 60)
    print(f"\n{'Mode':<12} {'Runtime (s)':<12} {'Mean (%)':<12} {'Std (%)':<12}")
    print("-" * 48)

    for mode, stats in results.items():
        print(
            f"{mode:<12} {stats['runtime']:<12.3f} "
            f"{stats['mean']*100:<12.2f} {stats['std']*100:<12.2f}"
        )

    # Verify both modes meet performance target
    print("\nPerformance Summary:")
    all_pass = True
    for mode, stats in results.items():
        if stats["runtime"] <= 2.0:
            print(f"  ✓ {mode}: {stats['runtime']:.3f}s (PASS)")
        else:
            print(f"  ✗ {mode}: {stats['runtime']:.3f}s (FAIL - exceeds 2s)")
            all_pass = False

    if all_pass:
        print("\n✓ All modes meet performance requirements!")
    else:
        print("\n✗ Some modes failed to meet performance requirements.")
        sys.exit(1)


if __name__ == "__main__":
    main()
