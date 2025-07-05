"""Configuration models for Financial Analysis Toolkit.

This module provides Pydantic models for loading and validating
simulation configurations from YAML files.
"""

from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ConfigModel(BaseModel):
    """Configuration model for retirement simulations.

    This model defines all configurable parameters for running simulations,
    allowing users to specify complex configurations via YAML files instead
    of many CLI flags.

    CLI arguments take precedence over config file values.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # Core simulation parameters
    strategy: str = Field("four_percent_rule", description="Withdrawal strategy to use")
    years: int = Field(30, ge=1, description="Number of years to simulate")
    paths: int = Field(1000, ge=1, description="Number of simulation paths to run")
    seed: int = Field(42, description="Random seed for reproducibility")

    # Portfolio parameters
    init_balance: float = Field(
        1_000_000.0, gt=0, description="Initial portfolio balance"
    )
    equity_pct: float = Field(
        0.6, ge=0, le=1, description="Equity allocation (0.0 to 1.0)"
    )
    fees_bps: int = Field(50, ge=0, description="Annual fees in basis points")

    # Market simulation parameters
    market_mode: str = Field(
        "lognormal", description="Market simulation mode (lognormal or bootstrap)"
    )

    # Output parameters
    output: str | None = Field(None, description="Output CSV file path")
    verbose: bool = Field(False, description="Enable verbose output")

    # Strategy-specific parameters
    # Constant percentage strategy
    percent: float = Field(
        0.05,
        ge=0,
        le=1,
        description="Percentage for constant_pct strategy (0.0 to 1.0)",
    )

    # Endowment strategy
    alpha: float = Field(
        0.7,
        ge=0,
        le=1,
        description="Alpha parameter for endowment strategy (weight for current portfolio)",
    )
    beta: float = Field(
        0.3,
        ge=0,
        le=1,
        description="Beta parameter for endowment strategy (weight for moving average)",
    )
    window: int = Field(
        3, ge=1, description="Window size for endowment strategy moving average"
    )

    # Guyton-Klinger strategy parameters
    initial_rate: float = Field(
        0.05,
        gt=0,
        lt=1,
        description="Initial withdrawal rate for Guyton-Klinger strategy",
    )
    guard_pct: float = Field(
        0.20, gt=0, lt=1, description="Guardrail percentage for Guyton-Klinger strategy"
    )
    raise_pct: float = Field(
        0.10, gt=0, lt=1, description="Raise percentage for Guyton-Klinger strategy"
    )
    cut_pct: float = Field(
        0.10, gt=0, lt=1, description="Cut percentage for Guyton-Klinger strategy"
    )

    # VPW strategy parameters
    vpw_table_path: str | None = Field(
        None, description="Path to custom VPW table YAML file"
    )

    def model_post_init(self, __context) -> None:
        """Validate interdependent fields after model initialization."""
        # Validate market mode
        if self.market_mode not in ["lognormal", "bootstrap"]:
            raise ValueError("market_mode must be 'lognormal' or 'bootstrap'")

        # Validate alpha + beta = 1.0 for endowment strategy
        if abs(self.alpha + self.beta - 1.0) > 1e-10:
            raise ValueError("alpha + beta must equal 1.0 for endowment strategy")

    @classmethod
    def from_yaml(cls, path: Path | str) -> Self:
        """Load ConfigModel from a YAML file.

        Args:
            path: Path to the YAML configuration file

        Returns:
            ConfigModel instance with loaded configuration

        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML is invalid
            ValidationError: If the config values are invalid
        """
        path = Path(path) if isinstance(path, str) else path

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        return cls(**data)

    def to_yaml(self, path: Path | str) -> None:
        """Save ConfigModel to a YAML file.

        Args:
            path: Path where to save the YAML configuration file
        """
        path = Path(path) if isinstance(path, str) else path

        # Convert model to dict, excluding None values for cleaner output
        data = self.model_dump(exclude_none=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)

    def merge_cli_args(self, **cli_args: Any) -> Self:
        """Create a new ConfigModel by merging CLI arguments.

        CLI arguments take precedence over config file values.
        Only non-None CLI arguments are used for merging.

        Args:
            **cli_args: CLI arguments to merge (only non-None values are used)

        Returns:
            New ConfigModel instance with merged values
        """
        # Start with current config values
        config_data = self.model_dump()

        # Override with non-None CLI arguments
        for key, value in cli_args.items():
            if value is not None and hasattr(self, key):
                config_data[key] = value

        return self.__class__(**config_data)
