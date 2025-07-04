"""Core domain models for financial simulations.

All models use Pydantic with strict validation and immutability settings.
Monetary fields are stored in nominal dollars.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class YearState(BaseModel):
    """Represents the financial state for a single year in the simulation."""

    model_config = ConfigDict(validate_assignment=True, frozen=True)

    year: int = Field(..., description="The calendar year")
    age: int = Field(..., ge=0, description="Age in years")
    balance: float = Field(..., description="Portfolio balance in nominal dollars")
    inflation: float = Field(..., description="Inflation rate as a decimal (e.g., 0.03 for 3%)")
    withdrawal_nominal: Optional[float] = Field(None, description="Withdrawal amount in nominal dollars")

    @classmethod
    def from_yaml(cls, path: Path | str) -> Self:
        """Load YearState from a YAML file."""
        path = Path(path) if isinstance(path, str) else path
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)


class PortfolioParams(BaseModel):
    """Parameters for portfolio configuration."""

    model_config = ConfigDict(validate_assignment=True, frozen=True)

    init_balance: float = Field(..., gt=0, description="Initial portfolio balance in nominal dollars")
    equity_pct: float = Field(..., ge=0, le=1, description="Equity allocation as a decimal (0-1)")
    fees_bps: int = Field(..., ge=0, description="Annual fees in basis points")
    seed: int = Field(42, description="Random number generator seed for reproducibility")

    @field_validator("equity_pct")
    @classmethod
    def validate_equity_pct(cls, v: float) -> float:
        """Ensure equity percentage is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(f"equity_pct must be between 0 and 1, got {v}")
        return v

    @classmethod
    def from_yaml(cls, path: Path | str) -> Self:
        """Load PortfolioParams from a YAML file."""
        path = Path(path) if isinstance(path, str) else path
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)


class LoanParams(BaseModel):
    """Parameters for loan calculations."""

    model_config = ConfigDict(validate_assignment=True, frozen=True)

    principal: float = Field(..., gt=0, description="Loan principal amount in nominal dollars")
    rate: float = Field(..., ge=0, description="Annual interest rate as a decimal (e.g., 0.05 for 5%)")
    term_months: int = Field(..., gt=0, description="Loan term in months")
    start: datetime = Field(..., description="Loan start date")

    def monthly_payment(self) -> float:
        """Calculate the fixed monthly payment amount.

        Uses the standard amortization formula:
        PMT = P × [r(1+r)^n] / [(1+r)^n - 1]

        where:
        - P = principal
        - r = monthly interest rate
        - n = number of months

        Returns:
            float: Monthly payment amount in nominal dollars
        """
        if self.rate == 0:
            # Handle zero interest rate case
            return self.principal / self.term_months

        monthly_rate = self.rate / 12
        n = self.term_months

        # Standard amortization formula
        payment = self.principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)

        return payment

    @classmethod
    def from_yaml(cls, path: Path | str) -> Self:
        """Load LoanParams from a YAML file."""
        path = Path(path) if isinstance(path, str) else path
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        # Convert datetime strings if needed
        if isinstance(data.get("start"), str):
            data["start"] = datetime.fromisoformat(data["start"])
        return cls(**data)