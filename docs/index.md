# Financial Analysis Toolkit

Welcome to the **Financial Analysis Toolkit** - an extensible, agent-friendly Python toolkit for simulating personal finance decisions with academic-quality rigor and production-grade code.

## 🎯 Overview

The Financial Analysis Toolkit empowers individuals, advisors, and autonomous LLM agents to simulate complex personal finance scenarios including:

- **Retirement planning** with multiple withdrawal strategies
- **Portfolio sustainability** analysis using Monte Carlo methods
- **Risk assessment** through thousands of simulation paths
- **Strategy comparison** with built-in visualization tools

## ✨ Key Features

### 🔧 Composable Architecture
- **Plugin-based strategies**: New withdrawal strategies drop in via entry points
- **Flexible configuration**: YAML files, CLI arguments, or Python API
- **Extensible design**: Add new simulators, data sources, or reporting modules

### 🎲 Robust Simulations
- **Deterministic results**: Seeded random number generation for reproducibility
- **High performance**: 10,000+ Monte Carlo paths in under 2 seconds
- **Multiple market models**: Lognormal and bootstrap simulation modes

### 🤖 LLM-Native Design
- **Machine-readable APIs**: DSPy signatures for agent integration
- **Rich CLI interface**: Typer-based command-line tools
- **Comprehensive documentation**: Auto-generated API references

### 📊 Advanced Analytics
- **Statistical analysis**: Success rates, percentiles, risk metrics
- **Rich visualizations**: Equity curves, probability bands, strategy comparisons
- **Export capabilities**: CSV, JSON, and plotting formats

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
```

## 📚 Documentation Sections

- **[Installation](installation.md)** - Setup and dependencies
- **[Quick Start](quick-start.md)** - Get up and running in minutes
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Examples](https://github.com/GGcarlson/Financial-Analysis-Toolkit/tree/main/examples)** - Sample configurations and Jupyter notebooks

## 🏗️ Architecture

```
capstone_finance/
├── core/           # Market simulator, inflation model, cash-flow ledger
├── strategies/     # Pluggable withdrawal strategies
├── reporting/      # Rich console tables, matplotlib/plotly charts
├── cli/            # Typer-based CLI interface
└── config/         # Configuration management
```

## 🧪 Available Strategies

The toolkit includes several built-in withdrawal strategies:

- **4% Rule (Bengen)**: Classic fixed withdrawal rate with inflation adjustment
- **Constant Percentage**: Dynamic percentage-based withdrawals
- **Endowment (Yale)**: Moving average approach for institutional-style management
- **Guyton-Klinger**: Guardrails-based dynamic adjustments
- **Custom Strategies**: Easy to implement via the plugin architecture

## 📈 Performance Benchmarks

- **Speed**: 10,000 40-year Monte Carlo paths in < 2 seconds
- **Accuracy**: ≤ 1% error vs established tools like FIRECalc
- **Coverage**: ≥90% test coverage with property-based testing
- **Reliability**: Deterministic results with seeded random number generation

## ⚠️ Financial Disclaimer

**This software is for educational purposes only and does not constitute financial advice.**

The calculations and simulations provided by this toolkit are based on historical data and mathematical models that may not accurately predict future market conditions. Users should:

- Consult with qualified financial professionals before making investment decisions
- Understand that past performance does not guarantee future results
- Consider their individual financial situation and risk tolerance
- Verify all calculations independently

## 🤝 Contributing

We welcome contributions! The toolkit is designed to be extensible:

- **New strategies**: Implement the `BaseStrategy` interface
- **Data sources**: Add new market data providers
- **Reporting**: Create custom visualization modules
- **Testing**: Add property-based tests for new features

See our [GitHub repository](https://github.com/GGcarlson/Financial-Analysis-Toolkit) for contribution guidelines.

## 📄 License

This project is licensed under the [MIT-0 License](https://github.com/GGcarlson/Financial-Analysis-Toolkit/blob/main/LICENSE) - see the LICENSE file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/GGcarlson/Financial-Analysis-Toolkit)
- [PyPI Package](https://pypi.org/project/capstone-finance/)
- [Issue Tracker](https://github.com/GGcarlson/Financial-Analysis-Toolkit/issues)
- [Discussions](https://github.com/GGcarlson/Financial-Analysis-Toolkit/discussions)

---

**Built with ❤️ for the financial planning community and LLM agents**