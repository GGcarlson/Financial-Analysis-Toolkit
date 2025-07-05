# Financial Analysis Toolkit

[![CI](https://github.com/GGcarlson/Financial-Analysis-Toolkit/workflows/CI/badge.svg)](https://github.com/GGcarlson/Financial-Analysis-Toolkit/actions)
[![codecov](https://codecov.io/gh/GGcarlson/Financial-Analysis-Toolkit/branch/master/graph/badge.svg)](https://codecov.io/gh/GGcarlson/Financial-Analysis-Toolkit)
[![PyPI version](https://badge.fury.io/py/capstone-finance.svg)](https://badge.fury.io/py/capstone-finance)
[![Python versions](https://img.shields.io/pypi/pyversions/capstone-finance.svg)](https://pypi.org/project/capstone-finance/)
[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-blue.svg)](https://opensource.org/licenses/MIT-0)

An extensible, agent-friendly Python toolkit that lets individuals, advisors, and autonomous LLM agents simulate personal-finance decisions—retirement withdrawals, mortgage refinancing, large purchases, etc.—with academic-quality rigor and production-grade code.

## 🚀 New to This? Start Here!

**👋 First time user?** Check out our [**Beginner Setup Guide**](BEGINNER_SETUP.md) for a complete step-by-step walkthrough, including:
- Platform-specific installation (Windows, Mac, Linux)
- Your first retirement simulation
- Common troubleshooting solutions
- Real examples with your own financial data

**⚡ Already familiar with Python?** Jump to the [Quick Start](#-quick-start) section below.

## 🎯 Vision

Build a toolkit that is:

- **Composable**: New strategies, simulators, or data feeds drop in via plug-ins—no fork required
- **Deterministic**: Given a seed + config, results are reproducible across machines
- **Fast**: 10,000 40-year Monte-Carlo paths in < 2 s on a modern laptop
- **LLM-native**: Public APIs documented with machine-readable DSPy signatures so Claude Code (or any agent) can reason about them

## 🚀 Quick Start

### Installation

```bash
pip install capstone-finance
```

### Basic Usage

```python
import capstone_finance as cf

# Create a retirement simulation
simulator = cf.RetirementSimulator(
    portfolio_value=1_000_000,
    strategy="4percent",
    years=30,
    seed=42
)

# Run simulation
results = simulator.run()
print(f"Success rate: {results.success_rate:.1%}")
```

### CLI Interface

```bash
# Run a retirement analysis
finance-cli retire --strategy four_percent_rule --years 30 --seed 42

# Use a configuration file
finance-cli retire --config examples/retirement_basic.yml

# Override config with CLI flags (CLI takes precedence)
finance-cli retire --config examples/retirement_basic.yml --years 40 --strategy guyton_klinger
```

### Configuration Files

Complex simulations can be defined in YAML configuration files instead of using many CLI flags:

```yaml
# retirement_config.yml
strategy: guyton_klinger
years: 30
paths: 1000
init_balance: 1000000.0
equity_pct: 0.6

# Guyton-Klinger specific parameters
initial_rate: 0.05
guard_pct: 0.20
raise_pct: 0.10
cut_pct: 0.10

output: "results.csv"
verbose: true
```

See [`examples/`](examples/) directory for complete configuration examples.

## 📊 Core Features

### Strategy Plugins
- **4% Rule (Bengen)**: Classic fixed withdrawal rate
- **Constant Percentage**: Dynamic percentage-based withdrawals
- **Endowment (Yale)**: Moving average approach
- **Guyton-Klinger**: Guardrails-based adjustments

### Scenario Simulators
- **Retirement Planning**: Portfolio longevity & success metrics
- **Refinance Analysis**: IRR, break-even, NPV calculations
- **Big Purchase Modeling**: Opportunity cost vs cash flow impact

### Data Sources
- Historical returns: Shiller S&P data via pandas-datareader
- Inflation: BLS CPI-U with monthly cache updates
- Yield curves: FRED DGS10 (optional, for glidepath calculations)

## 🏗️ Architecture

```
capstone_finance/
├── core/           # Market simulator, inflation model, cash-flow ledger
├── strategies/     # Pluggable withdrawal strategies
├── scenarios/      # Retirement, refinance, big purchase simulators
├── reporting/      # Rich console tables, matplotlib/plotly charts
├── cli/            # Typer-based CLI interface
└── signatures/     # DSPy JSON schemas for LLM integration
```

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/GGcarlson/Financial-Analysis-Toolkit.git
cd Financial-Analysis-Toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Development Commands

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run pre-commit hooks
pre-commit run --all-files
```

## 🧪 Testing

The project maintains ≥90% test coverage with:

- **Unit tests**: Core functionality and algorithms
- **Property-based tests**: Numerical stability with Hypothesis
- **Integration tests**: CLI and end-to-end workflows
- **Performance benchmarks**: Monte-Carlo simulation speed

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/core/

# Run tests matching pattern
pytest -k "test_strategy"

# Run with verbose output
pytest -v
```

## 📈 Performance

Target performance metrics:
- 10,000 40-year Monte-Carlo paths in < 2 seconds (P95)
- ≤ 1% error vs FIRECalc benchmarks on canonical cases
- Vectorized operations using NumPy/Pandas
- Optional Numba acceleration for heavy computation

## 🤖 LLM Integration

All public APIs are annotated with DSPy signatures for seamless agent integration:

```python
@signature("retirement_analysis",
           in_=RetirementParams,
           out=RetirementResults)
def analyze_retirement(params: RetirementParams) -> RetirementResults:
    """Analyze retirement portfolio sustainability."""
    # Implementation here
```

JSON manifests are auto-generated to `/signatures` for agent consumption.

## ⚠️ Financial Disclaimer

**This software is for educational purposes only and does not constitute financial advice.**

The calculations and simulations provided by this toolkit are based on historical data and mathematical models that may not accurately predict future market conditions. Users should:

- Consult with qualified financial professionals before making investment decisions
- Understand that past performance does not guarantee future results
- Consider their individual financial situation and risk tolerance
- Verify all calculations independently

## 🤝 Contributing

We welcome contributions! Please see our [contribution guidelines](CONTRIBUTING.md) for details.

### Adding a New Strategy

Adding a new withdrawal strategy requires ≤ 20 lines of code:

```python
from capstone_finance.strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def initial_withdrawal(self, state: YearState) -> float:
        return state.portfolio_value * 0.04

    def update_withdrawal(self, state: YearState) -> float:
        return self.last_withdrawal * (1 + state.inflation_rate)
```

## 📝 License

This project is licensed under the [MIT-0 License](LICENSE) - see the LICENSE file for details.

## 🔗 Links

- [Documentation](https://github.com/GGcarlson/Financial-Analysis-Toolkit#readme)
- [PyPI Package](https://pypi.org/project/capstone-finance/)
- [Issue Tracker](https://github.com/GGcarlson/Financial-Analysis-Toolkit/issues)
- [Discussions](https://github.com/GGcarlson/Financial-Analysis-Toolkit/discussions)

---

**Built with ❤️ for the financial planning community and LLM agents**
