"""Tests for the US Federal Tax Engine."""

import pytest

from capstone_finance.core.tax import (
    calc_tax,
    get_effective_tax_rate,
    get_marginal_tax_rate,
    create_tax_engine,
    SINGLE_BRACKETS_2025,
    MARRIED_BRACKETS_2025,
    STANDARD_DEDUCTION_2025,
)
from capstone_finance.core.ledger import CashFlowLedger
from capstone_finance.core.market import MarketSimulator
from capstone_finance.core.models import PortfolioParams
from capstone_finance.strategies.dummy import DummyStrategy
from capstone_finance.strategies.constant_percentage import ConstantPercentageStrategy


class TestTaxCalculation:
    """Tests for basic tax calculation functionality."""

    def test_golden_file_50k_single(self):
        """Golden-file test: $50k income should result in exactly $6,617 tax for single filers."""
        result = calc_tax(50_000, "single")
        expected = 6617.0
        assert result == expected, f"Expected ${expected}, got ${result}"

    def test_golden_file_edge_cases(self):
        """Test edge cases for tax calculation."""
        # Zero income
        assert calc_tax(0, "single") == 0.0
        assert calc_tax(0, "married") == 0.0
        
        # Negative income
        assert calc_tax(-1000, "single") == 0.0
        assert calc_tax(-1000, "married") == 0.0
        
        # Very small income
        assert calc_tax(1, "single") == 0.10
        assert calc_tax(1, "married") == 0.10

    def test_single_vs_married_brackets(self):
        """Test that married filing jointly has different (generally lower) rates."""
        test_income = 100_000
        
        single_tax = calc_tax(test_income, "single")
        married_tax = calc_tax(test_income, "married")
        
        # Married filing jointly should generally have lower tax on same income
        assert married_tax < single_tax
        
        print(f"Single tax on ${test_income}: ${single_tax}")
        print(f"Married tax on ${test_income}: ${married_tax}")

    def test_progressive_taxation(self):
        """Test that tax rate increases with income (progressive taxation)."""
        incomes = [25_000, 50_000, 100_000, 200_000]
        
        for filing_status in ["single", "married"]:
            previous_effective_rate = 0
            
            for income in incomes:
                tax = calc_tax(income, filing_status)
                effective_rate = tax / income
                
                # Effective tax rate should increase with income
                assert effective_rate >= previous_effective_rate, \
                    f"Tax should be progressive: {income} income has lower rate than previous"
                
                previous_effective_rate = effective_rate

    def test_invalid_filing_status(self):
        """Test that invalid filing status raises ValueError."""
        with pytest.raises(ValueError, match="filing_status must be"):
            calc_tax(50_000, "invalid")

    def test_tax_brackets_structure(self):
        """Test that tax brackets are properly structured."""
        # Test single brackets
        assert len(SINGLE_BRACKETS_2025) == 7  # 7 tax brackets
        assert SINGLE_BRACKETS_2025[0] == (0.10, 0)  # First bracket starts at 0
        
        # Verify brackets are in ascending order
        for i in range(1, len(SINGLE_BRACKETS_2025)):
            assert SINGLE_BRACKETS_2025[i][1] > SINGLE_BRACKETS_2025[i-1][1]
        
        # Test married brackets
        assert len(MARRIED_BRACKETS_2025) == 7  # 7 tax brackets
        assert MARRIED_BRACKETS_2025[0] == (0.10, 0)  # First bracket starts at 0

    def test_standard_deduction_simplified(self):
        """Test that standard deduction is set to 0 for simulation purposes."""
        assert STANDARD_DEDUCTION_2025["single"] == 0
        assert STANDARD_DEDUCTION_2025["married"] == 0


class TestTaxRateFunctions:
    """Tests for effective and marginal tax rate calculations."""

    def test_effective_tax_rate(self):
        """Test effective tax rate calculation."""
        income = 50_000
        tax = calc_tax(income, "single")
        expected_rate = tax / income
        
        actual_rate = get_effective_tax_rate(income, "single")
        assert abs(actual_rate - expected_rate) < 1e-10

    def test_marginal_tax_rate(self):
        """Test marginal tax rate calculation."""
        # Test income in 22% bracket
        income = 50_000  # Should be in 22% bracket for single filers
        marginal_rate = get_marginal_tax_rate(income, "single")
        assert marginal_rate == 0.22

        # Test income in 10% bracket
        income = 5_000  # Should be in 10% bracket
        marginal_rate = get_marginal_tax_rate(income, "single")
        assert marginal_rate == 0.10

    def test_zero_income_rates(self):
        """Test tax rates for zero income."""
        assert get_effective_tax_rate(0, "single") == 0.0
        assert get_marginal_tax_rate(0, "single") == 0.0


class TestTaxEngineIntegration:
    """Tests for tax engine integration with CashFlowLedger."""

    def test_create_tax_engine(self):
        """Test tax engine creation for different filing statuses."""
        # Test single filing
        engine_single = create_tax_engine("single")
        assert callable(engine_single)
        
        # Test that tax engine calculates correctly
        withdrawal = 50_000
        balance = 500_000  # Balance should not affect federal tax
        tax_owed = engine_single(withdrawal, balance)
        expected_tax = calc_tax(withdrawal, "single")
        assert tax_owed == expected_tax

        # Test married filing
        engine_married = create_tax_engine("married")
        tax_owed_married = engine_married(withdrawal, balance)
        expected_tax_married = calc_tax(withdrawal, "married")
        assert tax_owed_married == expected_tax_married

    def test_tax_engine_with_ledger(self):
        """Test tax engine integration with CashFlowLedger."""
        # Setup
        params = PortfolioParams(
            init_balance=500_000,
            equity_pct=0.6,
            fees_bps=50,
            seed=42
        )
        
        class FixedReturnSimulator:
            def generate(self, n_paths, n_years):
                import numpy as np
                return np.full((n_paths, n_years), 0.05, dtype=np.float64)  # 5% return
        
        simulator = FixedReturnSimulator()
        
        # Strategy that withdraws a fixed amount
        class FixedWithdrawalStrategy:
            def calculate_withdrawal(self, state, params):
                return 40_000  # $40k withdrawal
        
        strategy = FixedWithdrawalStrategy()
        
        # Run simulation without tax
        ledger_no_tax = CashFlowLedger(simulator, strategy, params, tax_engine=None)
        results_no_tax = ledger_no_tax.run(years=3, paths=1)
        
        # Run simulation with tax
        tax_engine = create_tax_engine("single")
        ledger_with_tax = CashFlowLedger(simulator, strategy, params, tax_engine=tax_engine)
        results_with_tax = ledger_with_tax.run(years=3, paths=1)
        
        # Compare final balances (with tax should be lower)
        final_balance_no_tax = results_no_tax[0][-1].balance
        final_balance_with_tax = results_with_tax[0][-1].balance
        
        assert final_balance_with_tax < final_balance_no_tax, \
            "Tax simulation should result in lower final balance"
        
        # The difference should be meaningful (taxes were paid)
        tax_impact = final_balance_no_tax - final_balance_with_tax
        expected_annual_tax = calc_tax(40_000, "single")
        
        print(f"Final balance without tax: ${final_balance_no_tax:,.2f}")
        print(f"Final balance with tax: ${final_balance_with_tax:,.2f}")
        print(f"Total tax impact: ${tax_impact:,.2f}")
        print(f"Expected annual tax: ${expected_annual_tax:,.2f}")
        
        # Tax impact should be substantial but not exact due to compounding effects
        assert tax_impact > expected_annual_tax, \
            "Total tax impact should be at least one year's worth of taxes"

    def test_low_income_no_tax_scenario(self):
        """Test that low-income scenario pays zero tax due to low withdrawals."""
        params = PortfolioParams(
            init_balance=100_000,
            equity_pct=0.6,
            fees_bps=50,
            seed=42
        )
        
        class FixedReturnSimulator:
            def generate(self, n_paths, n_years):
                import numpy as np
                return np.full((n_paths, n_years), 0.03, dtype=np.float64)  # 3% return
        
        simulator = FixedReturnSimulator()
        
        # Strategy that withdraws very little (below tax threshold)
        class LowWithdrawalStrategy:
            def calculate_withdrawal(self, state, params):
                return 5_000  # $5k withdrawal - very low
        
        strategy = LowWithdrawalStrategy()
        
        # Run simulation with tax
        tax_engine = create_tax_engine("single")
        ledger = CashFlowLedger(simulator, strategy, params, tax_engine=tax_engine)
        results = ledger.run(years=2, paths=1)
        
        # Verify that very low tax was paid (should be minimal)
        path = results[0]
        for year_state in path:
            withdrawal = year_state.withdrawal_nominal
            if withdrawal > 0:
                expected_tax = calc_tax(withdrawal, "single")
                # With $5k withdrawal, tax should be $500 (10% bracket)
                assert expected_tax == 500.0, f"Expected $500 tax on $5k, got ${expected_tax}"

    def test_balance_parameter_ignored(self):
        """Test that portfolio balance doesn't affect federal income tax calculation."""
        tax_engine = create_tax_engine("single")
        
        withdrawal = 50_000
        
        # Tax should be the same regardless of balance
        tax_low_balance = tax_engine(withdrawal, 100_000)
        tax_high_balance = tax_engine(withdrawal, 10_000_000)
        
        assert tax_low_balance == tax_high_balance, \
            "Federal income tax should not depend on portfolio balance"


class TestCLIIntegration:
    """Tests for CLI integration with tax engine."""

    def test_config_model_tax_validation(self):
        """Test ConfigModel validation for tax filing status."""
        from capstone_finance.config import ConfigModel
        
        # Valid values should work
        config = ConfigModel(tax_filing_status="single")
        assert config.tax_filing_status == "single"
        
        config = ConfigModel(tax_filing_status="married")
        assert config.tax_filing_status == "married"
        
        config = ConfigModel(tax_filing_status=None)
        assert config.tax_filing_status is None
        
        # Invalid value should raise error
        with pytest.raises(ValueError, match="tax_filing_status must be"):
            ConfigModel(tax_filing_status="invalid")

    def test_yaml_config_with_tax(self):
        """Test loading tax configuration from YAML."""
        import tempfile
        from pathlib import Path
        from capstone_finance.config import ConfigModel
        
        yaml_content = """
strategy: constant_pct
percent: 0.04
years: 30
paths: 1000
tax_filing_status: single
init_balance: 1000000
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            config = ConfigModel.from_yaml(temp_path)
            assert config.tax_filing_status == "single"
            assert config.strategy == "constant_pct"
            assert config.percent == 0.04
        finally:
            temp_path.unlink()  # Clean up temp file


class TestPerformanceAndEdgeCases:
    """Tests for performance and edge cases."""

    def test_large_income_calculation(self):
        """Test tax calculation for very large incomes."""
        large_income = 10_000_000  # $10 million
        
        single_tax = calc_tax(large_income, "single")
        married_tax = calc_tax(large_income, "married")
        
        # Should be in highest bracket (37%)
        assert single_tax > 3_000_000  # Should be substantial
        assert married_tax > 3_000_000  # Should be substantial
        assert married_tax < single_tax  # Married should still be lower

    def test_precision_and_rounding(self):
        """Test that tax calculations are properly rounded."""
        income = 50_123.45  # Odd amount
        tax = calc_tax(income, "single")
        
        # Should be rounded to 2 decimal places
        assert tax == round(tax, 2)

    def test_tax_engine_performance(self):
        """Test that tax engine is fast enough for simulation use."""
        import time
        
        tax_engine = create_tax_engine("single")
        
        # Time 1000 tax calculations
        start_time = time.time()
        for _ in range(1000):
            tax_engine(50_000, 1_000_000)
        elapsed_time = time.time() - start_time
        
        # Should complete 1000 calculations in well under 1 second
        assert elapsed_time < 0.1, f"Tax calculations too slow: {elapsed_time:.3f}s for 1000 calcs"