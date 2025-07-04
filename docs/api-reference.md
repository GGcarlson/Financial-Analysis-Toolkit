# API Reference

This page provides comprehensive documentation for the Financial Analysis Toolkit's Python API.

## Overview

The API is organized into several key modules:

- **[Core](#core)**: Fundamental simulation and data models
- **[Strategies](#strategies)**: Withdrawal strategy implementations
- **[Reporting](#reporting)**: Analysis and visualization tools
- **[CLI](#cli)**: Command-line interface components
- **[Config](#config)**: Configuration management

## Core

::: capstone_finance.core

### Models

::: capstone_finance.core.models

#### PortfolioParams

::: capstone_finance.core.models.PortfolioParams

#### YearState

::: capstone_finance.core.models.YearState

#### LoanParams

::: capstone_finance.core.models.LoanParams

### Market Simulator

::: capstone_finance.core.market

#### MarketSimulator

::: capstone_finance.core.market.MarketSimulator

### Cash Flow Ledger

::: capstone_finance.core.ledger

#### CashFlowLedger

::: capstone_finance.core.ledger.CashFlowLedger

## Strategies

::: capstone_finance.strategies

### Base Strategy

::: capstone_finance.strategies.base

#### BaseStrategy

::: capstone_finance.strategies.base.BaseStrategy

### Four Percent Rule

::: capstone_finance.strategies.four_percent_rule

#### FourPercentRule

::: capstone_finance.strategies.four_percent_rule.FourPercentRule

### Constant Percentage

::: capstone_finance.strategies.constant_percentage

#### ConstantPercentageStrategy

::: capstone_finance.strategies.constant_percentage.ConstantPercentageStrategy

### Guyton-Klinger

::: capstone_finance.strategies.guyton_klinger

#### GuytonKlingerStrategy

::: capstone_finance.strategies.guyton_klinger.GuytonKlingerStrategy

### Endowment Strategy

::: capstone_finance.strategies.endowment

#### EndowmentStrategy

::: capstone_finance.strategies.endowment.EndowmentStrategy

### Dummy Strategy

::: capstone_finance.strategies.dummy

#### DummyStrategy

::: capstone_finance.strategies.dummy.DummyStrategy

## Reporting

::: capstone_finance.reporting

### Summary Statistics

::: capstone_finance.reporting.summary

### Plotting

::: capstone_finance.reporting.plots

## CLI

::: capstone_finance.cli

## Config

::: capstone_finance.config

## Usage Examples

### Basic Simulation

```python
import capstone_finance as cf

# Create portfolio parameters
portfolio = cf.PortfolioParams(
    init_balance=1_000_000.0,
    equity_pct=0.6,
    fees_bps=50,
    seed=42
)

# Initialize components
strategy = cf.strategies.FourPercentRule()
market_sim = cf.MarketSimulator(mode="lognormal", seed=42)
ledger = cf.CashFlowLedger()

# Run simulation
results = ledger.run_simulation(
    params=portfolio,
    strategy=strategy,
    market_sim=market_sim,
    years=30,
    paths=1000
)

# Analyze results
from capstone_finance.reporting.summary import create_summary_statistics
summary = create_summary_statistics(results)
print(f"Success rate: {summary['success_rate']:.1%}")
```

### Custom Strategy Implementation

```python
from capstone_finance.strategies.base import BaseStrategy
from capstone_finance.core.models import PortfolioParams, YearState

class CustomStrategy(BaseStrategy):
    def __init__(self, initial_rate: float = 0.04, adjustment_factor: float = 0.1):
        self.initial_rate = initial_rate
        self.adjustment_factor = adjustment_factor
    
    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        if state is None:
            # First year withdrawal
            return params.init_balance * self.initial_rate
        
        # Subsequent years - adjust based on portfolio performance
        if state.balance > params.init_balance:
            # Portfolio grew, slightly increase withdrawal
            return state.balance * (self.initial_rate + self.adjustment_factor)
        else:
            # Portfolio declined, reduce withdrawal
            return state.balance * (self.initial_rate - self.adjustment_factor)
```

### Advanced Configuration

```python
# Create complex portfolio with multiple parameters
portfolio = cf.PortfolioParams(
    init_balance=1_500_000.0,
    equity_pct=0.75,
    fees_bps=30,  # Low-cost index funds
    seed=123
)

# Use Guyton-Klinger with custom parameters
strategy = cf.strategies.GuytonKlingerStrategy(
    initial_rate=0.045,
    guard_pct=0.20,
    raise_pct=0.15,
    cut_pct=0.10
)

# Bootstrap simulation using historical data
market_sim = cf.MarketSimulator(mode="bootstrap", seed=123)

# Run longer simulation with more paths
results = ledger.run_simulation(
    params=portfolio,
    strategy=strategy,
    market_sim=market_sim,
    years=40,
    paths=2000
)
```

### Visualization and Analysis

```python
import matplotlib.pyplot as plt
from capstone_finance.reporting.plots import create_equity_curve_plot
from capstone_finance.reporting.summary import create_summary_statistics, save_summary_csv

# Create visualizations
fig = create_equity_curve_plot(results)
plt.show()

# Generate detailed statistics
summary = create_summary_statistics(results)
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Median final balance: ${summary['median_final_balance']:,.0f}")
print(f"10th percentile: ${summary['p10_final_balance']:,.0f}")
print(f"90th percentile: ${summary['p90_final_balance']:,.0f}")

# Save results to CSV
save_summary_csv(results, "simulation_results.csv")
```

### Configuration File Usage

```python
from capstone_finance.config import ConfigModel

# Load configuration from YAML
config = ConfigModel.from_yaml("retirement_config.yml")

# Convert to portfolio parameters
portfolio = config.to_portfolio_params()

# Initialize strategy from config
strategy = config.get_strategy()

# Run simulation with config parameters
results = ledger.run_simulation(
    params=portfolio,
    strategy=strategy,
    market_sim=cf.MarketSimulator(mode=config.market_mode, seed=config.seed),
    years=config.years,
    paths=config.paths
)
```

## Type Hints and Annotations

The toolkit provides comprehensive type hints for better IDE support and code quality:

```python
from typing import Dict, List, Optional, Tuple
import pandas as pd
from capstone_finance.core.models import PortfolioParams, YearState

def analyze_portfolio(
    portfolio: PortfolioParams,
    strategies: List[str],
    years: int = 30,
    paths: int = 1000
) -> Dict[str, pd.DataFrame]:
    """
    Analyze portfolio performance across multiple strategies.
    
    Args:
        portfolio: Portfolio configuration parameters
        strategies: List of strategy names to test
        years: Number of years to simulate
        paths: Number of Monte Carlo paths
        
    Returns:
        Dictionary mapping strategy names to result DataFrames
    """
    results = {}
    
    for strategy_name in strategies:
        # Implementation here
        pass
    
    return results
```

## Error Handling

The toolkit provides specific exception types for different error conditions:

```python
from capstone_finance.core.exceptions import (
    PortfolioValidationError,
    StrategyNotFoundError,
    SimulationError
)

try:
    # Portfolio with invalid parameters
    portfolio = cf.PortfolioParams(
        init_balance=-1000,  # Invalid negative balance
        equity_pct=1.5,      # Invalid allocation > 100%
        fees_bps=-10,        # Invalid negative fees
        seed=42
    )
except PortfolioValidationError as e:
    print(f"Portfolio validation error: {e}")

try:
    # Non-existent strategy
    strategy = cf.strategies.get_strategy("non_existent_strategy")
except StrategyNotFoundError as e:
    print(f"Strategy not found: {e}")

try:
    # Simulation with invalid parameters
    results = ledger.run_simulation(
        params=portfolio,
        strategy=strategy,
        market_sim=market_sim,
        years=0,  # Invalid duration
        paths=0   # Invalid path count
    )
except SimulationError as e:
    print(f"Simulation error: {e}")
```

## Performance Considerations

### Optimizing Simulation Performance

```python
# For large-scale simulations, consider:

# 1. Use appropriate path counts
# Quick testing: 100-500 paths
# Standard analysis: 1000-2000 paths  
# High-precision: 5000+ paths

# 2. Vectorized operations when possible
import numpy as np

# 3. Use numba for heavy computations (optional dependency)
from numba import jit

@jit(nopython=True)
def fast_calculation(data: np.ndarray) -> np.ndarray:
    # Optimized calculation
    return data * 1.05

# 4. Consider market simulation mode
# "lognormal" - faster, parametric
# "bootstrap" - slower, uses historical data
```

### Memory Management

```python
# For large simulations, manage memory usage:

# Process results in chunks
def process_large_simulation(paths: int, chunk_size: int = 1000):
    all_results = []
    
    for i in range(0, paths, chunk_size):
        chunk_paths = min(chunk_size, paths - i)
        
        # Run simulation chunk
        results = ledger.run_simulation(
            params=portfolio,
            strategy=strategy,
            market_sim=market_sim,
            years=30,
            paths=chunk_paths
        )
        
        # Process and store results
        summary = create_summary_statistics(results)
        all_results.append(summary)
        
        # Clear memory
        del results
    
    return all_results
```

## Integration with Other Tools

### Pandas Integration

```python
import pandas as pd

# Results are returned as pandas DataFrames
results = ledger.run_simulation(...)

# Standard pandas operations work
print(results.head())
print(results.describe())

# Group by year for analysis
yearly_stats = results.groupby('year').agg({
    'balance': ['mean', 'median', 'std'],
    'withdrawal': ['mean', 'sum']
})

# Export to various formats
results.to_csv('results.csv')
results.to_excel('results.xlsx')
results.to_json('results.json')
```

### Matplotlib Integration

```python
import matplotlib.pyplot as plt

# Create custom visualizations
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot 1: Balance trajectories
yearly_medians = results.groupby('year')['balance'].median()
ax1.plot(yearly_medians.index, yearly_medians.values)
ax1.set_title('Median Portfolio Balance')
ax1.set_xlabel('Year')
ax1.set_ylabel('Balance ($)')

# Plot 2: Withdrawal amounts
yearly_withdrawals = results.groupby('year')['withdrawal'].mean()
ax2.plot(yearly_withdrawals.index, yearly_withdrawals.values)
ax2.set_title('Average Annual Withdrawal')
ax2.set_xlabel('Year')
ax2.set_ylabel('Withdrawal ($)')

plt.tight_layout()
plt.show()
```

### Jupyter Notebook Integration

```python
# Display rich output in Jupyter
from IPython.display import display, HTML
import pandas as pd

# Create interactive summary table
summary_df = pd.DataFrame({
    'Metric': ['Success Rate', 'Median Final Balance', 'Avg Withdrawal'],
    'Value': [f"{summary['success_rate']:.1%}", 
              f"${summary['median_final_balance']:,.0f}",
              f"${summary['avg_withdrawal']:,.0f}"]
})

display(HTML(summary_df.to_html(index=False)))

# Enable interactive plotting
%matplotlib widget
```

For more examples and advanced usage, see the [examples directory](https://github.com/GGcarlson/Financial-Analysis-Toolkit/tree/main/examples) and the [retirement walkthrough notebook](https://github.com/GGcarlson/Financial-Analysis-Toolkit/blob/main/examples/retirement_walkthrough.ipynb).