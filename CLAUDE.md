# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Financial Analysis Toolkit** (codename: capstone-finance) - an extensible, agent-friendly Python toolkit for simulating personal finance decisions with academic-quality rigor. The project targets Python 3.12+ and emphasizes LLM-native design with DSPy signatures.

## Architecture Overview

The codebase follows a modular, plugin-based architecture:

```
financial-toolkit/
├─ core/           # Market simulator, inflation model, cash-flow ledger
├─ strategies/     # Pluggable withdrawal strategies via entry-points
├─ scenarios/      # Retirement, refinance, big purchase simulators
├─ reporting/      # Rich console tables, matplotlib/plotly charts
├─ cli/            # Typer-based CLI interface
├─ signatures/     # DSPy JSON schemas for LLM integration
├─ configs/        # YAML configs → Pydantic models
├─ tests/          # pytest + hypothesis for numerical stability
└─ docs/           # MkDocs-Material + mkdocstrings
```

## Development Commands

### Setup & Dependencies
```bash
pip install -e .                    # Install in development mode
pip install -e ".[dev]"             # Install with dev dependencies
```

### Code Quality
```bash
black .                             # Format code
ruff check .                        # Lint code
mypy .                             # Type checking
pre-commit run --all-files         # Run all pre-commit hooks
```

### Testing
```bash
pytest                             # Run all tests
pytest -v                          # Verbose output
pytest tests/core/                 # Test specific module
pytest -k "test_strategy"          # Run tests matching pattern
pytest --cov                       # Coverage report (target ≥90%)
```

### CLI Development
```bash
finance-cli retire --help          # CLI help
finance-cli retire --strategy 4percent --years 30 --seed 42  # Example run
```

## Key Design Principles

### Strategy Plugin System
- All strategies inherit from `BaseStrategy` with `initial_withdrawal()` and `update_withdrawal()` methods
- Strategies registered via entry-points: `capstone_finance.strategies`
- Target: ≤20 lines of code to add new strategy

### Deterministic Results
- All simulations use seeded RNG (`numpy.random.Generator`)
- Results cached in `/outputs` with ISO timestamp + hash
- Given same seed + config, results must be reproducible across machines

### Performance Requirements
- Target: 10,000 40-year Monte-Carlo paths in <2 seconds
- Use vectorized operations (NumPy/Pandas)
- Optional Numba acceleration for heavy computation
- Provide `--quick` flag for faster approximate results

### LLM Integration
- All public APIs annotated with DSPy signatures: `@signature("name", in_=InputModel, out=OutputModel)`
- JSON manifests auto-generated to `/signatures`
- Pydantic v2 models for type safety and validation
- Google-style docstrings with examples required

## Data Handling

### Market Data Sources
- Primary: Shiller S&P data via pandas-datareader
- Fallback: Local CSV snapshots for offline operation
- Inflation: BLS CPI-U with monthly cache updates
- Yield curves: FRED DGS10 (stretch goal)

### Configuration
- YAML configs under `/configs` convertible to Pydantic models
- Assumptions documented in `/docs/assumptions.md` and version-pinned
- Support for external data feeds via plugins

## Financial Compliance

### Disclaimers Required
- "For educational use, no fiduciary advice" banner in CLI and docs
- Encourage users to consult certified financial planners
- Clear risk warnings for financial interpretations

### Validation Standards
- ≤1% error vs FIRECalc benchmarks on canonical retirement cases
- Property-based testing with hypothesis for numerical stability
- All financial calculations must have corresponding unit tests

## Testing Strategy

### Coverage Requirements
- Minimum 90% test coverage
- Property-based testing for numerical algorithms
- CLI integration tests for all command flags
- Performance benchmarks for Monte-Carlo simulations

### Test Organization
- `tests/core/` - Core engine tests
- `tests/strategies/` - Strategy plugin tests
- `tests/scenarios/` - Simulator tests
- `tests/cli/` - CLI interface tests

## Observability

### Logging
- Structured logging with configurable levels
- Optional Sentry DSN for error tracking
- Performance metrics for simulation runs

### Accessibility
- CLI colors auto-disable if NO_COLOR environment variable set
- Rich console output for better readability
- Export capabilities: CSV, Parquet, Feather formats

## Release Process

### Version Targets
- v0.1: Core engine + retirement MVP
- v0.2+: Additional strategies (VPW, Floor-Ceiling, Dynamic SWR)
- PyPI publication with GitHub Actions CI/CD

### Breaking Changes
- DSPy signature changes bump minor version
- Maintain backward compatibility for public APIs
- Document migration guides for major version updates
