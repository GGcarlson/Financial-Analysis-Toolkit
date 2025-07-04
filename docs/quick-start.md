# Quick Start Guide

Get up and running with the Financial Analysis Toolkit in just a few minutes!

## Installation

If you haven't installed the toolkit yet, see the [Installation Guide](installation.md).

```bash
pip install capstone-finance
```

## Your First Simulation

Let's run a basic retirement simulation using the classic 4% withdrawal rule.

### Using the CLI

```bash
# Run a basic 30-year retirement simulation
finance-cli retire --strategy four_percent_rule --years 30 --paths 1000 --seed 42

# This will output success rates, statistics, and a summary
```

### Using Python

```python
import capstone_finance as cf

# Create portfolio parameters
portfolio = cf.PortfolioParams(
    init_balance=1_000_000.0,  # $1M starting balance
    equity_pct=0.6,            # 60% stocks, 40% bonds
    fees_bps=50,               # 0.5% annual fees
    seed=42                    # For reproducible results
)

# Initialize strategy and market simulator
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
print(f"Median final balance: ${summary['median_final_balance']:,.0f}")
```

## Understanding the Output

The simulation provides several key metrics:

- **Success Rate**: Percentage of scenarios where the portfolio lasted the full duration
- **Final Balance Statistics**: Median, percentiles, and distribution of ending balances
- **Withdrawal Statistics**: Average withdrawals and inflation adjustments
- **Risk Metrics**: Probability of failure and timing analysis

## Configuration Files

For more complex scenarios, use YAML configuration files:

```yaml
# retirement_example.yml
strategy: four_percent_rule
years: 30
paths: 1000
seed: 42

# Portfolio settings
init_balance: 1000000.0
equity_pct: 0.6
fees_bps: 50

# Market simulation
market_mode: lognormal

# Output options
verbose: true
output: "my_results.csv"
```

Run with:

```bash
finance-cli retire --config retirement_example.yml
```

## Available Strategies

List all available withdrawal strategies:

```bash
finance-cli list-strategies
```

### Built-in Strategies

1. **Four Percent Rule** (`four_percent_rule`)
   - Classic 4% initial withdrawal with inflation adjustments
   - Conservative approach popular in FIRE community

2. **Constant Percentage** (`constant_pct`)
   - Withdraws fixed percentage of current balance each year
   - Dynamic approach that adjusts to market performance

3. **Guyton-Klinger** (`guyton_klinger`)
   - Guardrails-based approach with dynamic adjustments
   - Increases/decreases withdrawals based on portfolio performance

4. **Endowment Strategy** (`endowment`)
   - Moving average approach used by institutional investors
   - Smooths out market volatility

5. **Dummy Strategy** (`dummy`)
   - No withdrawals (for testing scenarios)

## Common Use Cases

### 1. Compare Multiple Strategies

```bash
# Test different strategies with same parameters
finance-cli retire --strategy four_percent_rule --years 30 --paths 1000 --seed 42
finance-cli retire --strategy constant_pct --percent 0.035 --years 30 --paths 1000 --seed 42
finance-cli retire --strategy guyton_klinger --years 30 --paths 1000 --seed 42
```

### 2. Sensitivity Analysis

```bash
# Test different equity allocations
finance-cli retire --strategy four_percent_rule --equity-pct 0.4 --years 30 --paths 1000 --seed 42
finance-cli retire --strategy four_percent_rule --equity-pct 0.6 --years 30 --paths 1000 --seed 42
finance-cli retire --strategy four_percent_rule --equity-pct 0.8 --years 30 --paths 1000 --seed 42
```

### 3. Long-term Planning

```bash
# Test extended retirement periods
finance-cli retire --strategy four_percent_rule --years 40 --paths 2000 --seed 42
```

### 4. Export Results

```bash
# Save results to CSV for further analysis
finance-cli retire --strategy four_percent_rule --years 30 --paths 1000 --output results.csv
```

## CLI Options Reference

### Core Parameters

- `--strategy`: Withdrawal strategy to use
- `--years`: Number of years to simulate
- `--paths`: Number of Monte Carlo paths (default: 1000)
- `--seed`: Random seed for reproducibility

### Portfolio Parameters

- `--init-balance`: Starting portfolio balance (default: 1,000,000)
- `--equity-pct`: Equity allocation as decimal (default: 0.6)
- `--fees-bps`: Annual fees in basis points (default: 50)

### Strategy-Specific Parameters

- `--percent`: For constant percentage strategy
- `--initial-rate`: For Guyton-Klinger initial withdrawal rate
- `--guard-pct`: For Guyton-Klinger guardrail percentage

### Output Options

- `--verbose`: Show detailed output
- `--output`: Save results to CSV file
- `--config`: Load configuration from YAML file

## Python API Basics

### Key Classes

```python
# Core models
from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.core.ledger import CashFlowLedger
from capstone_finance.core.market import MarketSimulator

# Strategies
from capstone_finance.strategies.four_percent_rule import FourPercentRule
from capstone_finance.strategies.constant_percentage import ConstantPercentageStrategy
from capstone_finance.strategies.guyton_klinger import GuytonKlingerStrategy

# Reporting
from capstone_finance.reporting.summary import create_summary_statistics
from capstone_finance.reporting.plots import create_equity_curve_plot
```

### Basic Workflow

```python
# 1. Define portfolio parameters
portfolio = PortfolioParams(
    init_balance=1_000_000.0,
    equity_pct=0.6,
    fees_bps=50,
    seed=42
)

# 2. Choose strategy
strategy = FourPercentRule()

# 3. Create market simulator
market_sim = MarketSimulator(mode="lognormal", seed=42)

# 4. Run simulation
ledger = CashFlowLedger()
results = ledger.run_simulation(
    params=portfolio,
    strategy=strategy, 
    market_sim=market_sim,
    years=30,
    paths=1000
)

# 5. Analyze results
summary = create_summary_statistics(results)
```

## Best Practices

### 1. Use Sufficient Monte Carlo Paths

```bash
# For quick testing
finance-cli retire --paths 100

# For reliable results
finance-cli retire --paths 1000

# For high-precision analysis
finance-cli retire --paths 5000
```

### 2. Set Random Seeds for Reproducibility

```bash
# Always use --seed for consistent results
finance-cli retire --strategy four_percent_rule --seed 42
```

### 3. Start with Conservative Estimates

```bash
# Conservative scenario
finance-cli retire --strategy four_percent_rule --equity-pct 0.5 --years 35

# Aggressive scenario  
finance-cli retire --strategy constant_pct --percent 0.05 --equity-pct 0.8 --years 30
```

### 4. Use Configuration Files for Complex Scenarios

Create reusable configuration files for different scenarios:

```yaml
# conservative_retirement.yml
strategy: four_percent_rule
years: 35
paths: 2000
init_balance: 1000000.0
equity_pct: 0.5
fees_bps: 30
seed: 42
```

## Troubleshooting

### Common Issues

1. **Strategy not found**: Make sure you're using the correct strategy name from `finance-cli list-strategies`

2. **Import errors**: Ensure you're in the right virtual environment and the package is installed

3. **Slow simulations**: Reduce the number of paths for testing, increase for final analysis

4. **Inconsistent results**: Always use the same seed value for reproducible results

### Getting Help

```bash
# General help
finance-cli --help

# Command-specific help
finance-cli retire --help

# List available strategies
finance-cli list-strategies
```

## Next Steps

- Explore the [Examples](https://github.com/GGcarlson/Financial-Analysis-Toolkit/tree/main/examples) directory
- Check out the [retirement walkthrough Jupyter notebook](https://github.com/GGcarlson/Financial-Analysis-Toolkit/blob/main/examples/retirement_walkthrough.ipynb)
- Read the [API Reference](api-reference.md) for detailed documentation
- Learn about [creating custom strategies](https://github.com/GGcarlson/Financial-Analysis-Toolkit#adding-a-new-strategy)

## Sample Scenarios

### Early Retirement (FIRE)

```bash
# Conservative FIRE scenario
finance-cli retire --strategy four_percent_rule --init-balance 1000000 --years 40 --equity-pct 0.7 --seed 42
```

### Traditional Retirement

```bash
# Traditional retirement with pension supplement
finance-cli retire --strategy constant_pct --percent 0.025 --init-balance 750000 --years 25 --equity-pct 0.5 --seed 42
```

### Aggressive Growth

```bash
# High growth, high risk scenario
finance-cli retire --strategy guyton_klinger --init-balance 500000 --years 35 --equity-pct 0.9 --seed 42
```

Ready to dive deeper? Check out the [API Reference](api-reference.md) for complete documentation!