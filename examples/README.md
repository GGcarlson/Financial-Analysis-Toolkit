# Configuration Examples

This directory contains sample YAML configuration files for the Financial Analysis Toolkit.

## Available Examples

### `retirement_basic.yml`
A simple retirement simulation using the 4% rule with standard parameters:
- $1M initial portfolio
- 60% equity allocation
- 30-year simulation with 1,000 paths

### `retirement_advanced.yml`
An advanced simulation showcasing the endowment strategy:
- $2M initial portfolio
- 80% equity allocation (higher risk)
- 40-year simulation with 5,000 paths
- Bootstrap market simulation
- Custom endowment strategy parameters

### `guyton_klinger_example.yml`
Demonstrates the Guyton-Klinger guardrails strategy:
- $1.5M initial portfolio
- 65% equity allocation
- 35-year simulation with 2,000 paths
- Customized guardrail parameters (±25% with 15%/12% adjustments)

## Usage

Run any configuration with:

```bash
finance-cli retire --config examples/[config_file].yml
```

You can override any configuration value with CLI flags:

```bash
# Use config but override years and strategy
finance-cli retire --config examples/retirement_basic.yml --years 40 --strategy guyton_klinger
```

CLI arguments always take precedence over config file values.