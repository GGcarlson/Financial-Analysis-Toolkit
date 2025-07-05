"""Tests for Variable Percentage Withdrawal (VPW) strategy."""

import tempfile
from pathlib import Path

import pytest
import yaml

from capstone_finance.core.models import PortfolioParams, YearState
from capstone_finance.strategies.vpw import VariablePercentageWithdrawal


class TestVariablePercentageWithdrawal:
    """Tests for Variable Percentage Withdrawal strategy."""

    def test_vpw_basic_withdrawal_60_percent_equity(self):
        """Test basic VPW withdrawal with 60% equity allocation."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)

        # For 60% equity at age 65, withdrawal should be 3.6%
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.036  # 3.6% of current balance
        assert abs(withdrawal - expected) < 1e-10

    def test_vpw_basic_withdrawal_40_percent_equity(self):
        """Test basic VPW withdrawal with 40% equity allocation."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.4, fees_bps=50)
        state = YearState(year=2024, age=70, balance=800_000.0, inflation=0.02)

        # For 40% equity at age 70, withdrawal should be 4.5%
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 800_000.0 * 0.045  # 4.5% of current balance
        assert withdrawal == expected

    def test_vpw_basic_withdrawal_80_percent_equity(self):
        """Test basic VPW withdrawal with 80% equity allocation."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.8, fees_bps=50)
        state = YearState(year=2024, age=75, balance=1_200_000.0, inflation=0.025)

        # For 80% equity at age 75, withdrawal should be 4.2%
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_200_000.0 * 0.042  # 4.2% of current balance
        assert withdrawal == expected

    def test_vpw_basic_withdrawal_20_percent_equity(self):
        """Test basic VPW withdrawal with 20% equity allocation."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.2, fees_bps=50)
        state = YearState(year=2024, age=80, balance=900_000.0, inflation=0.03)

        # For 20% equity at age 80, withdrawal should be 6.8%
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 900_000.0 * 0.068  # 6.8% of current balance
        assert withdrawal == expected

    def test_vpw_no_state_defaults_to_age_65(self):
        """Test VPW with no state defaults to age 65."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)

        # Without state, should use age 65 and initial balance
        withdrawal = strategy.calculate_withdrawal(None, params)
        expected = 1_000_000.0 * 0.036  # 3.6% for 60% equity at age 65
        assert abs(withdrawal - expected) < 1e-10

    def test_vpw_equity_allocation_rounding(self):
        """Test that equity allocation is rounded to nearest table key."""
        strategy = VariablePercentageWithdrawal()
        
        # Test 55% equity (should round to 60%)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.55, fees_bps=50)
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.036  # Should use 60% table
        assert abs(withdrawal - expected) < 1e-10

        # Test 30% equity (should round to 20%)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.30, fees_bps=50)
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.044  # Should use 20% table (4.4% at age 65)
        assert abs(withdrawal - expected) < 1e-10

    def test_vpw_age_below_minimum(self):
        """Test VPW with age below minimum in table."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=40, balance=1_000_000.0, inflation=0.03)

        # Age 40 is below minimum (45), should use minimum age rate
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.025  # Should use age 45 rate (2.5% for 60% equity)
        assert withdrawal == expected

    def test_vpw_age_above_maximum(self):
        """Test VPW with age above maximum in table."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=100, balance=1_000_000.0, inflation=0.03)

        # Age 100 is above maximum (95), should use maximum rate capped at 10%
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.10  # Should be capped at 10%
        assert withdrawal == expected

    def test_vpw_age_interpolation(self):
        """Test VPW with age that requires interpolation."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        
        # Age 64.5 should interpolate between age 64 (3.5%) and age 65 (3.6%)
        state = YearState(year=2024, age=64, balance=1_000_000.0, inflation=0.03)
        withdrawal_64 = strategy.calculate_withdrawal(state, params)
        
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        withdrawal_65 = strategy.calculate_withdrawal(state, params)
        
        # Verify the values are different and in expected range
        assert withdrawal_64 < withdrawal_65
        assert abs(withdrawal_64 - 1_000_000.0 * 0.035) < 1e-10  # 3.5% for age 64
        assert abs(withdrawal_65 - 1_000_000.0 * 0.036) < 1e-10  # 3.6% for age 65

    def test_vpw_custom_table_loading(self):
        """Test loading custom VPW table from YAML file."""
        custom_table = {
            50: {  # 50% equity allocation
                60: 3.0,
                65: 3.5,
                70: 4.0,
                75: 4.5,
                80: 5.0,
            }
        }
        
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(custom_table, f)
            temp_path = Path(f.name)
        
        try:
            # Load strategy with custom table
            strategy = VariablePercentageWithdrawal(vpw_table_path=temp_path)
            params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.5, fees_bps=50)
            state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
            
            withdrawal = strategy.calculate_withdrawal(state, params)
            expected = 1_000_000.0 * 0.035  # 3.5% from custom table
            assert withdrawal == expected
            
        finally:
            # Clean up temporary file
            temp_path.unlink()

    def test_vpw_custom_table_direct(self):
        """Test providing custom VPW table directly."""
        custom_table = {
            60: {  # 60% equity allocation
                65: 2.5,  # Different from default
                70: 3.0,
                75: 3.5,
            }
        }
        
        strategy = VariablePercentageWithdrawal(custom_table=custom_table)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.025  # 2.5% from custom table
        assert withdrawal == expected

    def test_vpw_withdrawal_percentage_cap(self):
        """Test that withdrawal percentage is capped at 10%."""
        # Create a custom table with high withdrawal rates
        custom_table = {
            60: {
                90: 15.0,  # 15% - should be capped at 10%
                95: 20.0,  # 20% - should be capped at 10%
            }
        }
        
        strategy = VariablePercentageWithdrawal(custom_table=custom_table)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=95, balance=1_000_000.0, inflation=0.03)
        
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.10  # Should be capped at 10%
        assert abs(withdrawal - expected) < 1e-10

    def test_vpw_different_balance_amounts(self):
        """Test VPW with various balance amounts."""
        strategy = VariablePercentageWithdrawal()
        
        test_cases = [
            (100_000.0, 3_600.0),   # 100k * 3.6%
            (500_000.0, 18_000.0),  # 500k * 3.6%
            (1_000_000.0, 36_000.0), # 1M * 3.6%
            (2_000_000.0, 72_000.0), # 2M * 3.6%
        ]
        
        for balance, expected_withdrawal in test_cases:
            params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
            state = YearState(year=2024, age=65, balance=balance, inflation=0.03)
            withdrawal = strategy.calculate_withdrawal(state, params)
            assert abs(withdrawal - expected_withdrawal) < 1e-10

    def test_vpw_str_representation(self):
        """Test string representation of VPW strategy."""
        strategy = VariablePercentageWithdrawal()
        assert str(strategy) == "VariablePercentageWithdrawal"

    def test_vpw_repr_representation(self):
        """Test repr representation of VPW strategy."""
        strategy = VariablePercentageWithdrawal()
        assert repr(strategy) == "VariablePercentageWithdrawal(table_source=default)"
        
        # Test with custom table
        custom_table = {60: {65: 3.0}}
        strategy_custom = VariablePercentageWithdrawal(custom_table=custom_table)
        assert repr(strategy_custom) == "VariablePercentageWithdrawal(table_source=custom)"

    def test_vpw_inheritance(self):
        """Test that VPW strategy properly inherits from BaseStrategy."""
        from capstone_finance.strategies.base import BaseStrategy
        
        strategy = VariablePercentageWithdrawal()
        assert isinstance(strategy, BaseStrategy)
        assert hasattr(strategy, "calculate_withdrawal")

    def test_vpw_non_negative_withdrawals(self):
        """Test that VPW strategy never returns negative withdrawals."""
        strategy = VariablePercentageWithdrawal()
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        
        # Test with zero balance
        state = YearState(year=2024, age=65, balance=0.0, inflation=0.03)
        withdrawal = strategy.calculate_withdrawal(state, params)
        assert withdrawal == 0.0
        
        # Test with various ages and balances
        test_cases = [
            (45, 1_000_000.0),
            (65, 500_000.0),
            (85, 100_000.0),
            (95, 50_000.0),
        ]
        
        for age, balance in test_cases:
            state = YearState(year=2024, age=age, balance=balance, inflation=0.03)
            withdrawal = strategy.calculate_withdrawal(state, params)
            assert withdrawal >= 0.0

    def test_vpw_default_table_coverage(self):
        """Test that default VPW tables cover expected age ranges."""
        strategy = VariablePercentageWithdrawal()
        
        # Test that all default equity allocations are present
        expected_allocations = [20, 40, 60, 80]
        for allocation in expected_allocations:
            assert allocation in strategy.vpw_tables
            
        # Test that age ranges are reasonable
        for allocation, age_table in strategy.vpw_tables.items():
            ages = list(age_table.keys())
            assert min(ages) <= 45  # Should start at or before age 45
            assert max(ages) >= 95  # Should go to at least age 95
            
            # Test that withdrawal percentages are reasonable
            for age, pct in age_table.items():
                assert 0.0 <= pct <= 10.0  # Between 0% and 10%

    def test_vpw_age_progression_increases(self):
        """Test that withdrawal percentages generally increase with age."""
        strategy = VariablePercentageWithdrawal()
        
        # Test for each equity allocation
        for allocation in [20, 40, 60, 80]:
            age_table = strategy.vpw_tables[allocation]
            ages = sorted(age_table.keys())
            
            # Check that withdrawal percentages generally increase
            for i in range(len(ages) - 1):
                current_age = ages[i]
                next_age = ages[i + 1]
                current_pct = age_table[current_age]
                next_pct = age_table[next_age]
                
                # Allow for some small decreases due to rounding
                assert next_pct >= current_pct - 0.1

    def test_vpw_equity_allocation_inverse_relationship(self):
        """Test that higher equity allocations have lower withdrawal rates."""
        strategy = VariablePercentageWithdrawal()
        params_list = [
            PortfolioParams(init_balance=1_000_000.0, equity_pct=0.2, fees_bps=50),
            PortfolioParams(init_balance=1_000_000.0, equity_pct=0.4, fees_bps=50),
            PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50),
            PortfolioParams(init_balance=1_000_000.0, equity_pct=0.8, fees_bps=50),
        ]
        
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        
        withdrawals = []
        for params in params_list:
            withdrawal = strategy.calculate_withdrawal(state, params)
            withdrawals.append(withdrawal)
        
        # Higher equity should generally result in lower withdrawal rates
        # (20% equity should have highest withdrawal, 80% equity should have lowest)
        assert withdrawals[0] > withdrawals[1]  # 20% > 40%
        assert withdrawals[1] > withdrawals[2]  # 40% > 60%
        assert withdrawals[2] > withdrawals[3]  # 60% > 80%

    def test_vpw_string_key_conversion(self):
        """Test that string keys in YAML are properly converted to integers."""
        import tempfile
        import yaml
        
        # Create custom table with string keys (as would come from YAML)
        string_key_data = {
            "60": {  # String equity allocation key
                "65": 3.0,  # String age key
                "70": 4.0,
            }
        }
        
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(string_key_data, f)
            temp_path = Path(f.name)
        
        try:
            strategy = VariablePercentageWithdrawal(vpw_table_path=temp_path)
            params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
            state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
            
            withdrawal = strategy.calculate_withdrawal(state, params)
            expected = 1_000_000.0 * 0.03  # 3.0% from custom table
            assert abs(withdrawal - expected) < 1e-10
            
        finally:
            temp_path.unlink()

    def test_vpw_intermediate_interpolation(self):
        """Test interpolation with various intermediate ages."""
        # Create a custom table with wider gaps to test interpolation
        custom_table = {
            60: {
                60: 3.0,
                70: 5.0,  # 2% increase over 10 years = 0.2% per year
            }
        }
        
        strategy = VariablePercentageWithdrawal(custom_table=custom_table)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        
        # Test various ages that require interpolation
        test_cases = [
            (62, 3.4),  # 60 + (2/10) * 2.0 = 3.4%
            (65, 4.0),  # 60 + (5/10) * 2.0 = 4.0%
            (68, 4.6),  # 60 + (8/10) * 2.0 = 4.6%
        ]
        
        for age, expected_pct in test_cases:
            state = YearState(year=2024, age=age, balance=1_000_000.0, inflation=0.03)
            withdrawal = strategy.calculate_withdrawal(state, params)
            expected = 1_000_000.0 * (expected_pct / 100.0)
            assert abs(withdrawal - expected) < 1e-10, f"Age {age}: expected {expected}, got {withdrawal}"

    def test_vpw_empty_custom_table_error_handling(self):
        """Test behavior with malformed custom tables."""
        import tempfile
        import yaml
        
        # Test with empty table
        empty_data = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(empty_data, f)
            temp_path = Path(f.name)
        
        try:
            strategy = VariablePercentageWithdrawal(vpw_table_path=temp_path)
            params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
            state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
            
            # This should raise an error or use default behavior
            # Since we have an empty table, this should fail
            with pytest.raises(ValueError):
                strategy.calculate_withdrawal(state, params)
                
        finally:
            temp_path.unlink()

    def test_vpw_mixed_key_types(self):
        """Test handling of mixed integer and string keys."""
        # Create table with both int and string keys
        mixed_table = {
            60: {  # int key
                65: 3.0,
                "70": 4.0,  # string key
            },
            "80": {  # string key
                65: 2.5,
                70: 3.5,
            }
        }
        
        strategy = VariablePercentageWithdrawal(custom_table=mixed_table)
        params = PortfolioParams(init_balance=1_000_000.0, equity_pct=0.6, fees_bps=50)
        state = YearState(year=2024, age=65, balance=1_000_000.0, inflation=0.03)
        
        withdrawal = strategy.calculate_withdrawal(state, params)
        expected = 1_000_000.0 * 0.03  # Should find 60% table, age 65 = 3.0%
        assert abs(withdrawal - expected) < 1e-10