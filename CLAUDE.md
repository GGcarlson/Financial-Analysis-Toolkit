# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Financial Analysis Toolkit** (codename: capstone-finance) - an extensible, agent-friendly Python toolkit for simulating personal finance decisions with academic-quality rigor. The project targets Python 3.11+ and emphasizes modular, plugin-based architecture for withdrawal strategies.

## Current Architecture

The codebase implements a core simulation engine with pluggable withdrawal strategies:

```
src/capstone_finance/
├── core/              # Market simulator, models, cash-flow ledger
│   ├── models.py      # Pydantic models: PortfolioParams, YearState, LoanParams
│   ├── market.py      # MarketSimulator for Monte Carlo simulations
│   └── ledger.py      # CashFlowLedger for running simulations
├── strategies/        # Pluggable withdrawal strategies via entry-points
│   ├── base.py        # BaseStrategy abstract class
│   ├── dummy.py       # DummyStrategy (0% withdrawal)
│   ├── four_percent_rule.py    # 4% rule with inflation adjustment
│   ├── constant_percentage.py # Constant percentage of current balance
│   ├── endowment.py   # Yale endowment moving-average strategy
│   ├── guyton_klinger.py       # Dynamic strategy with guardrails
│   └── vpw.py         # Variable Percentage Withdrawal (age-based)
├── reporting/         # Result analysis and visualization
│   ├── plots.py       # Equity curve and visualization generation
│   └── summary.py     # Statistical summaries and CSV exports
├── config.py          # Configuration management with Pydantic
└── cli.py             # Typer-based CLI interface

tests/
├── core/              # Core functionality tests
├── strategies/        # Strategy-specific tests + property-based fuzz testing
│   ├── property_fuzz_test.py  # Hypothesis-based tests for all strategies
│   └── test_*.py      # Individual strategy unit tests
├── reporting/         # Reporting module tests
└── cli/               # CLI integration tests

examples/              # Configuration examples and notebooks
├── *.yml              # Strategy configuration examples
└── *.ipynb            # Jupyter notebook demonstrations
```

## Development Commands

### Setup & Dependencies
```bash
# Clone and set up development environment
git clone https://github.com/GGcarlson/Financial-Analysis-Toolkit.git
cd Financial-Analysis-Toolkit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install package after entry point changes (required for strategy discovery)
pip install -e .
```

### Code Quality
```bash
black .                             # Format code
ruff check .                        # Lint code
ruff check . --fix                  # Auto-fix linting issues
mypy .                             # Type checking
mypy src/capstone_finance/         # Type check specific module
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage (target ≥90%)
pytest --cov

# Run specific test modules
pytest tests/core/                 # Core functionality
pytest tests/strategies/           # All strategy tests
pytest tests/cli/                  # CLI tests

# Run property-based tests (validates all strategies)
pytest tests/strategies/property_fuzz_test.py

# Run tests matching pattern
pytest -k "test_strategy"          # Pattern matching
pytest -k "constant_percentage"    # Specific strategy

# Verbose output and quiet mode
pytest -v                          # Verbose
pytest -q                          # Quiet (good for CI)

# Run single test method
pytest tests/strategies/test_constant_percentage.py::TestConstantPercentageStrategy::test_withdrawal_tracks_current_balance
```

### CLI Development and Testing
```bash
# List available strategies
finance-cli list-strategies

# Run retirement simulation examples
finance-cli retire --help
finance-cli retire --strategy four_percent_rule --years 30 --paths 1000
finance-cli retire --strategy constant_pct --percent 0.03 --years 25 --paths 500
finance-cli retire --strategy vpw --years 30 --paths 1000 --verbose
finance-cli retire --strategy vpw --vpw-table examples/custom_vpw_table.yml

# Export results to CSV
finance-cli retire --strategy constant_pct --output results.csv

# Use configuration files
finance-cli retire --config examples/vpw_example.yml
finance-cli retire --config examples/guyton_klinger_example.yml
```

## Strategy Plugin Architecture

### Core Components

1. **BaseStrategy Abstract Class** (`strategies/base.py`):
   - All strategies must inherit from `BaseStrategy`
   - Single required method: `calculate_withdrawal(state, params) -> float`
   - `state` can be `None` for simple strategies
   - `params` contains portfolio configuration

2. **Entry Point Registration** (`pyproject.toml`):
   ```toml
   [project.entry-points."capstone_finance.strategies"]
   dummy = "capstone_finance.strategies.dummy:DummyStrategy"
   four_percent_rule = "capstone_finance.strategies.four_percent_rule:FourPercentRule"
   constant_pct = "capstone_finance.strategies.constant_percentage:ConstantPercentageStrategy"
   endowment = "capstone_finance.strategies.endowment:EndowmentStrategy"
   guyton_klinger = "capstone_finance.strategies.guyton_klinger:GuytonKlingerStrategy"
   vpw = "capstone_finance.strategies.vpw:VariablePercentageWithdrawal"
   ```

3. **Strategy Discovery** (`cli.py`):
   - Uses `importlib.metadata.entry_points()` for runtime discovery
   - Strategies automatically available in CLI and tests
   - Must reinstall package (`pip install -e .`) after adding new entry points

### Strategy Implementation Pattern

```python
from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, param: float = 0.05):
        self.param = param
    
    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        if state is None:
            return params.init_balance * self.param
        return state.balance * self.param
```

### Adding New Strategies

1. Create strategy file in `src/capstone_finance/strategies/`
2. Add entry point to `pyproject.toml`
3. Export in `src/capstone_finance/strategies/__init__.py`
4. Handle strategy parameters in CLI (`cli.py`) if needed
5. Create unit tests in `tests/strategies/test_[strategy_name].py`
6. Run `pip install -e .` to register entry point
7. Verify with property-based tests: `pytest tests/strategies/property_fuzz_test.py`

## Core Models and Data Flow

### Key Pydantic Models (`core/models.py`)
- **`PortfolioParams`**: Initial balance, equity allocation, fees, seed
- **`YearState`**: Year, age, current balance, inflation rate, withdrawal amount  
- **`LoanParams`**: Principal, rate, term, start date (with payment calculation)

### Simulation Flow
1. **CLI** → **Strategy instantiation** → **MarketSimulator** → **CashFlowLedger**
2. **MarketSimulator**: Generates market returns using seeded Monte Carlo
3. **CashFlowLedger**: Runs multiple simulation paths, applies strategy withdrawals
4. **Results**: DataFrame with year-by-year balance/withdrawal data

## Property-Based Testing Framework

The project includes comprehensive property-based testing using Hypothesis (`tests/strategies/property_fuzz_test.py`):

### Financial Properties Validated
- **No NaN values**: Withdrawal calculations never return NaN
- **Non-negative withdrawals**: All withdrawal amounts ≥ 0
- **Inflation monotonicity**: Higher inflation → higher/same withdrawals
- **Deterministic behavior**: Same inputs → same outputs
- **Reasonable bounds**: Strategy-specific upper limits
- **None state handling**: Graceful handling when state is None

### Test Configuration
- **1,000+ test cases** per property per strategy
- **30-second timeout** per test to maintain fast CI
- **Automatic strategy discovery**: Tests all registered strategies
- **Parameterized execution**: Each property tested against all strategies

### Strategy Classification for Property Tests
Strategies are classified by their behavior for property-based testing bounds:

```python
# In property_fuzz_test.py
if strategy_name in ["constant_pct", "endowment", "vpw"]:
    # These strategies can withdraw up to 100% of current balance
    max_reasonable = state.balance * 1.0
else:
    # Other strategies should not exceed 100% of initial balance per year
    max_reasonable = params.init_balance * 1.0
```

**Current Balance Dependent**: `constant_pct`, `endowment`, `vpw`
**Initial Balance Dependent**: `four_percent_rule`, `guyton_klinger`, `dummy`

## CLI Integration Patterns

### Strategy-Specific Parameters
The CLI handles strategy-specific parameters through conditional instantiation:

```python
# In cli.py
if final_config.strategy == "constant_pct":
    strategy_instance = strategies[final_config.strategy](percentage=final_config.percent)
elif final_config.strategy == "endowment":
    strategy_instance = strategies[final_config.strategy](
        alpha=final_config.alpha, beta=final_config.beta, window=final_config.window
    )
elif final_config.strategy == "guyton_klinger":
    strategy_instance = strategies[final_config.strategy](
        initial_rate=final_config.initial_rate, guard_pct=final_config.guard_pct,
        raise_pct=final_config.raise_pct, cut_pct=final_config.cut_pct
    )
elif final_config.strategy == "vpw":
    vpw_table_path = Path(final_config.vpw_table_path) if final_config.vpw_table_path else None
    strategy_instance = strategies[final_config.strategy](vpw_table_path=vpw_table_path)
else:
    strategy_instance = strategies[final_config.strategy]()
```

### Adding CLI Parameters for New Strategies
1. Add parameter to `retire()` function with `typer.Option()`
2. Add parameter to `ConfigModel` class in `config.py`
3. Add parameter to CLI args dictionary in `retire()` function
4. Extend strategy instantiation logic with parameter handling
5. Update help text and examples

**Example Pattern for Custom Parameters:**
- Simple parameters: Add to both CLI options and ConfigModel
- File-based parameters: Handle Path conversion in strategy instantiation
- Complex parameters: Use nested Pydantic models or YAML configuration

## Data Sources and Configuration

### Market Data
- **Primary**: Historical data via pandas-datareader (when implemented)
- **Current**: Simulated market returns in MarketSimulator
- **Modes**: "lognormal" and "bootstrap" simulation modes

### Configuration Management
- **Pydantic models** for type safety and validation (`ConfigModel` in `config.py`)
- **YAML support** via `from_yaml()` class methods on models
- **Immutable models** with `frozen=True` for reproducibility
- **CLI priority**: CLI arguments override config file values
- **Configuration examples** in `examples/` directory for all strategies

### Configuration File Patterns
```yaml
# Basic structure in examples/*.yml
strategy: "strategy_name"
years: 30
paths: 1000
seed: 42
init_balance: 1000000.0
equity_pct: 0.6
fees_bps: 50
market_mode: "lognormal"
output: "results.csv"
verbose: true

# Strategy-specific parameters
strategy_param: value
custom_file_path: "path/to/file.yml"
```

**Available Examples:**
- `vpw_example.yml`: Variable Percentage Withdrawal with default tables
- `vpw_custom_example.yml`: VPW with custom table file
- `guyton_klinger_example.yml`: Dynamic withdrawal with guardrails
- `retirement_basic.yml` / `retirement_advanced.yml`: General configurations

## Performance and Determinism

### Reproducibility Requirements
- All simulations use **seeded RNG** (`numpy.random.Generator`)
- Same seed + config → identical results across machines
- Random seed configurable via CLI `--seed` parameter

### Performance Targets
- Target: 10,000 40-year Monte-Carlo paths in <2 seconds
- Use vectorized operations (NumPy/Pandas)
- Property-based tests complete in <30 seconds total

## Testing Standards

### Coverage Requirements
- Minimum 90% test coverage maintained
- Property-based testing for numerical stability
- CLI integration tests for all command flags

### Test Organization and Patterns
- **Unit tests**: Individual strategy behavior and edge cases
- **Property tests**: Cross-strategy financial invariants  
- **Integration tests**: CLI functionality and end-to-end workflows
- **Performance tests**: Simulation speed benchmarks (when implemented)

### Running Test Suites
```bash
# Full test suite (recommended before commits)
pytest --cov

# Strategy-only tests (faster during strategy development)
pytest tests/strategies/

# Property-based tests (validates all strategies)
pytest tests/strategies/property_fuzz_test.py

# Single strategy development
pytest tests/strategies/test_constant_percentage.py -v
```

## Financial Compliance and Validation

### Disclaimers Required
- "For educational use, no fiduciary advice" in CLI and documentation
- Encourage consulting certified financial planners
- Clear risk warnings for financial interpretations

### Validation Standards
- Property-based testing ensures numerical stability
- All financial calculations must have corresponding unit tests
- Cross-validation against established financial planning tools (target: ≤1% error vs FIRECalc)

## Development Workflow

### Pre-commit Requirements
1. **Format**: `black .`
2. **Lint**: `ruff check . --fix`
3. **Type check**: `mypy .`
4. **Test**: `pytest --cov`
5. **Strategy registration**: `pip install -e .` (if entry points changed)

### Common Development Tasks
- **Adding strategy**: Follow strategy implementation pattern above
- **CLI enhancement**: Modify `cli.py` with new options/commands
- **Model changes**: Update `core/models.py` and associated tests
- **Performance optimization**: Profile with simulation benchmarks

### Debugging and Troubleshooting
- **Strategy not discovered**: Check entry point registration + `pip install -e .`
- **Property tests failing**: Review strategy edge cases and bounds
- **CLI parameter errors**: Verify validation logic and parameter handling
- **Import errors**: Ensure proper `__init__.py` exports and package structure