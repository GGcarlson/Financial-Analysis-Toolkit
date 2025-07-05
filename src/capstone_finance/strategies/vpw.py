"""Variable Percentage Withdrawal (VPW) strategy implementation.

Based on the VPW methodology that uses age-based withdrawal percentages
with different asset allocation tables. The strategy includes default
VPW tables and supports custom table loading via YAML files.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from ..core.models import PortfolioParams, YearState
from .base import BaseStrategy


class VariablePercentageWithdrawal(BaseStrategy):
    """Variable Percentage Withdrawal (VPW) strategy.
    
    This strategy uses age-based withdrawal percentages that vary based on
    the portfolio's equity allocation. The withdrawal percentage generally
    increases with age and decreases with higher equity allocations.
    
    The strategy includes default VPW tables for 20%, 40%, 60%, and 80%
    equity allocations, and supports loading custom tables from YAML files.
    """
    
    # Default VPW table data for different equity allocations
    DEFAULT_VPW_TABLES = {
        20: {  # 20% equity allocation
            45: 3.0, 46: 3.0, 47: 3.1, 48: 3.1, 49: 3.2, 50: 3.2,
            51: 3.3, 52: 3.3, 53: 3.4, 54: 3.4, 55: 3.5, 56: 3.6,
            57: 3.6, 58: 3.7, 59: 3.8, 60: 3.9, 61: 4.0, 62: 4.1,
            63: 4.2, 64: 4.3, 65: 4.4, 66: 4.5, 67: 4.6, 68: 4.8,
            69: 4.9, 70: 5.0, 71: 5.2, 72: 5.3, 73: 5.5, 74: 5.6,
            75: 5.8, 76: 6.0, 77: 6.2, 78: 6.4, 79: 6.6, 80: 6.8,
            81: 7.1, 82: 7.3, 83: 7.6, 84: 7.9, 85: 8.2, 86: 8.5,
            87: 8.8, 88: 9.2, 89: 9.6, 90: 10.0, 91: 10.0, 92: 10.0,
            93: 10.0, 94: 10.0, 95: 10.0
        },
        40: {  # 40% equity allocation
            45: 2.7, 46: 2.7, 47: 2.8, 48: 2.8, 49: 2.9, 50: 2.9,
            51: 3.0, 52: 3.0, 53: 3.1, 54: 3.1, 55: 3.2, 56: 3.2,
            57: 3.3, 58: 3.4, 59: 3.4, 60: 3.5, 61: 3.6, 62: 3.7,
            63: 3.8, 64: 3.9, 65: 4.0, 66: 4.1, 67: 4.2, 68: 4.3,
            69: 4.4, 70: 4.5, 71: 4.7, 72: 4.8, 73: 4.9, 74: 5.1,
            75: 5.2, 76: 5.4, 77: 5.6, 78: 5.8, 79: 6.0, 80: 6.2,
            81: 6.4, 82: 6.6, 83: 6.9, 84: 7.2, 85: 7.5, 86: 7.8,
            87: 8.1, 88: 8.5, 89: 8.9, 90: 9.3, 91: 9.7, 92: 10.0,
            93: 10.0, 94: 10.0, 95: 10.0
        },
        60: {  # 60% equity allocation
            45: 2.5, 46: 2.5, 47: 2.6, 48: 2.6, 49: 2.6, 50: 2.7,
            51: 2.7, 52: 2.8, 53: 2.8, 54: 2.9, 55: 2.9, 56: 3.0,
            57: 3.0, 58: 3.1, 59: 3.1, 60: 3.2, 61: 3.3, 62: 3.3,
            63: 3.4, 64: 3.5, 65: 3.6, 66: 3.7, 67: 3.8, 68: 3.9,
            69: 4.0, 70: 4.1, 71: 4.2, 72: 4.3, 73: 4.4, 74: 4.6,
            75: 4.7, 76: 4.9, 77: 5.0, 78: 5.2, 79: 5.4, 80: 5.6,
            81: 5.8, 82: 6.0, 83: 6.3, 84: 6.5, 85: 6.8, 86: 7.1,
            87: 7.4, 88: 7.8, 89: 8.2, 90: 8.6, 91: 9.0, 92: 9.5,
            93: 10.0, 94: 10.0, 95: 10.0
        },
        80: {  # 80% equity allocation
            45: 2.3, 46: 2.3, 47: 2.4, 48: 2.4, 49: 2.4, 50: 2.5,
            51: 2.5, 52: 2.5, 53: 2.6, 54: 2.6, 55: 2.7, 56: 2.7,
            57: 2.8, 58: 2.8, 59: 2.9, 60: 2.9, 61: 3.0, 62: 3.0,
            63: 3.1, 64: 3.2, 65: 3.3, 66: 3.3, 67: 3.4, 68: 3.5,
            69: 3.6, 70: 3.7, 71: 3.8, 72: 3.9, 73: 4.0, 74: 4.1,
            75: 4.2, 76: 4.4, 77: 4.5, 78: 4.7, 79: 4.8, 80: 5.0,
            81: 5.2, 82: 5.4, 83: 5.6, 84: 5.9, 85: 6.1, 86: 6.4,
            87: 6.7, 88: 7.1, 89: 7.4, 90: 7.8, 91: 8.3, 92: 8.8,
            93: 9.3, 94: 9.8, 95: 10.0
        }
    }
    
    def __init__(
        self,
        vpw_table_path: Optional[Path] = None,
        custom_table: Optional[Dict[int, Dict[int, float]]] = None
    ):
        """Initialize the VPW strategy.
        
        Args:
            vpw_table_path: Path to custom VPW table YAML file
            custom_table: Custom VPW table data directly provided
        """
        if vpw_table_path is not None:
            self.vpw_tables = self._load_custom_table(vpw_table_path)
        elif custom_table is not None:
            self.vpw_tables = custom_table
        else:
            self.vpw_tables = self.DEFAULT_VPW_TABLES
    
    def _load_custom_table(self, path: Path) -> Dict[int, Dict[int, float]]:
        """Load custom VPW table from YAML file.
        
        Args:
            path: Path to YAML file containing VPW table data
            
        Returns:
            Dictionary mapping equity allocation percentages to age-based withdrawal rates
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        
        # Convert string keys to integers if needed
        converted_data = {}
        for equity_pct, age_table in data.items():
            equity_key = int(equity_pct) if isinstance(equity_pct, str) else equity_pct
            converted_age_table = {}
            for age, rate in age_table.items():
                age_key = int(age) if isinstance(age, str) else age
                converted_age_table[age_key] = float(rate)
            converted_data[equity_key] = converted_age_table
        
        return converted_data
    
    def _get_equity_allocation_key(self, equity_pct: float) -> int:
        """Get the closest equity allocation key from available tables.
        
        Args:
            equity_pct: Equity allocation as a decimal (0-1)
            
        Returns:
            Integer key for the closest equity allocation table
        """
        equity_percentage = int(equity_pct * 100)
        available_keys = list(self.vpw_tables.keys())
        
        # Handle empty table case
        if not available_keys:
            raise ValueError("VPW table is empty - no equity allocations available")
        
        # Ensure all keys are integers (convert if needed)
        int_keys = []
        for key in available_keys:
            if isinstance(key, str):
                int_keys.append(int(key))
            else:
                int_keys.append(key)
        
        # Find the closest key
        closest_key = min(int_keys, key=lambda x: abs(x - equity_percentage))
        return closest_key
    
    def _get_withdrawal_percentage(self, age: int, equity_allocation_key: int) -> float:
        """Get withdrawal percentage for given age and equity allocation.
        
        Args:
            age: Current age
            equity_allocation_key: Equity allocation key (e.g., 20, 40, 60, 80)
            
        Returns:
            Withdrawal percentage as a decimal (e.g., 0.04 for 4%)
        """
        age_table = self.vpw_tables[equity_allocation_key]
        
        # If exact age is in table, return it (capped at 10%)
        if age in age_table:
            return min(age_table[age], 10.0) / 100.0
        
        # Handle ages below minimum
        min_age = min(age_table.keys())
        if age < min_age:
            return min(age_table[min_age], 10.0) / 100.0
        
        # Handle ages above maximum
        max_age = max(age_table.keys())
        if age > max_age:
            return min(age_table[max_age], 10.0) / 100.0  # Cap at 10%
        
        # Linear interpolation for ages between table entries
        ages = sorted(age_table.keys())
        for i in range(len(ages) - 1):
            if ages[i] <= age <= ages[i + 1]:
                lower_age, upper_age = ages[i], ages[i + 1]
                lower_rate, upper_rate = age_table[lower_age], age_table[upper_age]
                
                # Linear interpolation
                weight = (age - lower_age) / (upper_age - lower_age)
                interpolated_rate = lower_rate + weight * (upper_rate - lower_rate)
                return min(interpolated_rate, 10.0) / 100.0
        
        # Fallback (should not reach here)
        return 0.04  # Default to 4%
    
    def calculate_withdrawal(
        self, state: YearState | None, params: PortfolioParams
    ) -> float:
        """Calculate VPW withdrawal amount.
        
        Args:
            state: Current year state including age and balance
            params: Portfolio parameters including equity allocation
            
        Returns:
            Withdrawal amount in nominal dollars
        """
        if state is None:
            # If no state provided, use default assumptions
            age = 65  # Default retirement age
            balance = params.init_balance
        else:
            age = state.age
            balance = state.balance
        
        # Get the appropriate equity allocation key
        equity_key = self._get_equity_allocation_key(params.equity_pct)
        
        # Get the withdrawal percentage for this age and equity allocation
        withdrawal_pct = self._get_withdrawal_percentage(age, equity_key)
        
        # Calculate withdrawal amount
        withdrawal_amount = balance * withdrawal_pct
        
        return withdrawal_amount
    
    def __repr__(self) -> str:
        """Return detailed string representation."""
        table_source = "default" if self.vpw_tables == self.DEFAULT_VPW_TABLES else "custom"
        return f"VariablePercentageWithdrawal(table_source={table_source})"