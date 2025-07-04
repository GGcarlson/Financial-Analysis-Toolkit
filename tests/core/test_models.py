"""Tests for core domain models."""

from datetime import datetime

import pytest
import yaml
from pydantic import ValidationError

from capstone_finance.core import LoanParams, PortfolioParams, YearState


class TestYearState:
    """Tests for YearState model."""

    def test_valid_year_state(self):
        """Test creating a valid YearState."""
        state = YearState(
            year=2024,
            age=65,
            balance=1_000_000.0,
            inflation=0.03,
            withdrawal_nominal=40_000.0,
        )
        assert state.year == 2024
        assert state.age == 65
        assert state.balance == 1_000_000.0
        assert state.inflation == 0.03
        assert state.withdrawal_nominal == 40_000.0

    def test_year_state_without_withdrawal(self):
        """Test YearState with optional withdrawal field."""
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        assert state.withdrawal_nominal is None

    def test_year_state_immutable(self):
        """Test that YearState is frozen/immutable."""
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        with pytest.raises(ValidationError):
            state.balance = 2_000_000.0

    def test_year_state_negative_age_validation(self):
        """Test that negative age raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            YearState(year=2024, age=-1, balance=1_000_000.0, inflation=0.03)
        assert "age" in str(exc_info.value)

    def test_year_state_from_yaml(self, tmp_path):
        """Test loading YearState from YAML file."""
        yaml_data = {
            "year": 2024,
            "age": 65,
            "balance": 1_000_000.0,
            "inflation": 0.03,
            "withdrawal_nominal": 40_000.0,
        }

        yaml_file = tmp_path / "year_state.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_data, f)

        state = YearState.from_yaml(yaml_file)
        assert state.year == 2024
        assert state.balance == 1_000_000.0


class TestPortfolioParams:
    """Tests for PortfolioParams model."""

    def test_valid_portfolio_params(self):
        """Test creating valid PortfolioParams."""
        params = PortfolioParams(
            init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50, seed=12345
        )
        assert params.init_balance == 1_000_000.0
        assert params.equity_pct == 0.6
        assert params.fees_bps == 50
        assert params.seed == 12345

    def test_portfolio_params_default_seed(self):
        """Test default seed value."""
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        assert params.seed == 42

    def test_portfolio_params_immutable(self):
        """Test that PortfolioParams is frozen/immutable."""
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        with pytest.raises(ValidationError):
            params.fees_bps = 100

    def test_portfolio_params_negative_balance_validation(self):
        """Test that negative balance raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioParams(init_balance=-1000.0, equity_pct=0.6, fees_bps=50)
        assert "init_balance" in str(exc_info.value)

    def test_portfolio_params_invalid_equity_pct_below_zero(self):
        """Test that equity_pct < 0 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioParams(init_balance=1_000_000.0, equity_pct=-0.1, fees_bps=50)
        assert "equity_pct" in str(exc_info.value)

    def test_portfolio_params_invalid_equity_pct_above_one(self):
        """Test that equity_pct > 1 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioParams(init_balance=1_000_000.0, equity_pct=1.1, fees_bps=50)
        assert "equity_pct" in str(exc_info.value)

    def test_portfolio_params_equity_pct_boundaries(self):
        """Test equity_pct boundary values 0 and 1."""
        # Test 0% equity
        params_zero = PortfolioParams(
            init_balance=1_000_000.0, equity_pct=0.0, fees_bps=50
        )
        assert params_zero.equity_pct == 0.0

        # Test 100% equity
        params_one = PortfolioParams(
            init_balance=1_000_000.0, equity_pct=1.0, fees_bps=50
        )
        assert params_one.equity_pct == 1.0

    def test_portfolio_params_negative_fees_validation(self):
        """Test that negative fees raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=-10)
        assert "fees_bps" in str(exc_info.value)

    def test_portfolio_params_from_yaml(self, tmp_path):
        """Test loading PortfolioParams from YAML file."""
        yaml_data = {
            "init_balance": 2_000_000.0,
            "equity_pct": 0.7,
            "fees_bps": 75,
            "seed": 99999,
        }

        yaml_file = tmp_path / "portfolio_params.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_data, f)

        params = PortfolioParams.from_yaml(yaml_file)
        assert params.init_balance == 2_000_000.0
        assert params.equity_pct == 0.7
        assert params.fees_bps == 75
        assert params.seed == 99999

    def test_portfolio_params_fee_assignment_creates_copy(self):
        """Test that attempting to modify fees creates a validation error (proving immutability)."""
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Since the model is frozen, any assignment will raise a ValidationError
        with pytest.raises(ValidationError):
            params.fees_bps = 100

        # The original value should remain unchanged
        assert params.fees_bps == 50


class TestLoanParams:
    """Tests for LoanParams model."""

    def test_valid_loan_params(self):
        """Test creating valid LoanParams."""
        start_date = datetime(2024, 1, 1)
        loan = LoanParams(
            principal=300_000.0, rate=0.05, term_months=360, start=start_date
        )
        assert loan.principal == 300_000.0
        assert loan.rate == 0.05
        assert loan.term_months == 360
        assert loan.start == start_date

    def test_loan_params_immutable(self):
        """Test that LoanParams is frozen/immutable."""
        loan = LoanParams(
            principal=300_000.0, rate=0.05, term_months=360, start=datetime(2024, 1, 1)
        )
        with pytest.raises(ValidationError):
            loan.principal = 400_000.0

    def test_loan_params_negative_principal_validation(self):
        """Test that negative principal raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LoanParams(
                principal=-100_000.0,
                rate=0.05,
                term_months=360,
                start=datetime(2024, 1, 1),
            )
        assert "principal" in str(exc_info.value)

    def test_loan_params_negative_rate_validation(self):
        """Test that negative rate raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LoanParams(
                principal=300_000.0,
                rate=-0.05,
                term_months=360,
                start=datetime(2024, 1, 1),
            )
        assert "rate" in str(exc_info.value)

    def test_loan_params_negative_term_validation(self):
        """Test that negative term raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LoanParams(
                principal=300_000.0,
                rate=0.05,
                term_months=-360,
                start=datetime(2024, 1, 1),
            )
        assert "term_months" in str(exc_info.value)

    def test_monthly_payment_calculation(self):
        """Test monthly payment calculation with standard loan."""
        loan = LoanParams(
            principal=300_000.0,
            rate=0.05,  # 5% annual
            term_months=360,  # 30 years
            start=datetime(2024, 1, 1),
        )

        # Expected payment calculated using standard formula
        # For $300k at 5% for 30 years: ~$1,610.46
        payment = loan.monthly_payment()
        assert abs(payment - 1610.46) < 0.01

    def test_monthly_payment_zero_rate(self):
        """Test monthly payment with zero interest rate."""
        loan = LoanParams(
            principal=300_000.0,
            rate=0.0,  # 0% interest
            term_months=360,
            start=datetime(2024, 1, 1),
        )

        # With 0% interest, payment = principal / months
        payment = loan.monthly_payment()
        assert payment == 300_000.0 / 360
        assert payment == 833.33333333333333

    def test_monthly_payment_short_term(self):
        """Test monthly payment with short term loan."""
        loan = LoanParams(
            principal=10_000.0,
            rate=0.06,  # 6% annual
            term_months=12,  # 1 year
            start=datetime(2024, 1, 1),
        )

        # For $10k at 6% for 1 year: ~$860.66
        payment = loan.monthly_payment()
        assert abs(payment - 860.66) < 0.01

    def test_loan_params_from_yaml(self, tmp_path):
        """Test loading LoanParams from YAML file."""
        yaml_data = {
            "principal": 400_000.0,
            "rate": 0.045,
            "term_months": 180,
            "start": "2024-06-01T00:00:00",
        }

        yaml_file = tmp_path / "loan_params.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_data, f)

        loan = LoanParams.from_yaml(yaml_file)
        assert loan.principal == 400_000.0
        assert loan.rate == 0.045
        assert loan.term_months == 180
        assert loan.start == datetime(2024, 6, 1)

    def test_loan_params_from_yaml_datetime_object(self, tmp_path):
        """Test loading LoanParams from YAML with datetime object."""
        yaml_data = {
            "principal": 250_000.0,
            "rate": 0.04,
            "term_months": 240,
            "start": datetime(2025, 1, 1),
        }

        yaml_file = tmp_path / "loan_params_dt.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_data, f)

        loan = LoanParams.from_yaml(yaml_file)
        assert loan.start == datetime(2025, 1, 1)
