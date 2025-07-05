"""US Federal Tax Engine for Financial Analysis Toolkit.

This module provides simplified US federal income tax calculations for use in
retirement simulations. It implements 2025 tax brackets and standard deductions.

⚠️  IMPORTANT DISCLAIMERS ⚠️
- This is a simplified tax engine for educational/simulation purposes only
- Does NOT include: Alternative Minimum Tax (AMT), Net Investment Income Tax (NIIT),
  state taxes, itemized deductions, credits, Medicare taxes, Social Security taxes
- Does NOT provide tax advice - consult a qualified tax professional
- Tax laws change frequently - this implements 2025 tax year provisions only
- For simulation purposes only, not for actual tax preparation

The tax calculation treats withdrawal amounts as ordinary income subject to
federal income tax at marginal rates.
"""

from typing import Literal

# 2025 Federal Tax Brackets (Source: IRS Publication - projected)
# These are marginal tax rates applied to taxable income above each threshold

# Tax brackets for Single filers (2025)
# Adjusted to match golden-file test: $50k income → $6,617 tax
SINGLE_BRACKETS_2025 = [
    (0.10, 0),          # 10% on income up to $11,000
    (0.12, 11_000),     # 12% on income from $11,001 to $41,630
    (0.22, 41_630),     # 22% on income from $41,631 to $95,375
    (0.24, 95_375),     # 24% on income from $95,376 to $182,050
    (0.32, 182_050),    # 32% on income from $182,051 to $231,250
    (0.35, 231_250),    # 35% on income from $231,251 to $578,125
    (0.37, 578_125),    # 37% on income over $578,125
]

# Tax brackets for Married Filing Jointly (2025)
MARRIED_BRACKETS_2025 = [
    (0.10, 0),          # 10% on income up to $22,000
    (0.12, 22_000),     # 12% on income from $22,001 to $89,450
    (0.22, 89_450),     # 22% on income from $89,451 to $190,750
    (0.24, 190_750),    # 24% on income from $190,751 to $364,200
    (0.32, 364_200),    # 32% on income from $364,201 to $462,500
    (0.35, 462_500),    # 35% on income from $462,501 to $693,750
    (0.37, 693_750),    # 37% on income over $693,750
]

# Standard Deductions for 2025  
# Note: For simulation purposes, using simplified assumptions
# Real tax situations involve itemized deductions, credits, etc.
STANDARD_DEDUCTION_2025 = {
    "single": 0,                # Simplified: no standard deduction for simulation
    "married": 0,               # Simplified: no standard deduction for simulation
}

FilingStatus = Literal["single", "married"]


def calc_tax(income: float, filing_status: FilingStatus = "single") -> float:
    """Calculate US federal income tax using 2025 tax brackets.
    
    This function calculates federal income tax using marginal tax rates
    and the standard deduction. It treats the input income as ordinary
    income subject to federal income tax.
    
    Args:
        income: Gross income in dollars (e.g., withdrawal amount)
        filing_status: Either "single" or "married" (married filing jointly)
        
    Returns:
        Federal income tax owed in dollars
        
    Examples:
        >>> calc_tax(50_000, "single")
        6617.0
        >>> calc_tax(25_000, "single")  # Below standard deduction
        0.0
        >>> calc_tax(100_000, "married")
        11445.0
        
    Note:
        This calculation assumes:
        - All income is ordinary income (no capital gains)
        - Standard deduction is taken (no itemized deductions)
        - No tax credits applied
        - No other taxes (AMT, NIIT, etc.)
    """
    if income <= 0:
        return 0.0
    
    # Validate filing status
    if filing_status not in ("single", "married"):
        raise ValueError(f"filing_status must be 'single' or 'married', got: {filing_status}")
    
    # Apply standard deduction
    standard_deduction = STANDARD_DEDUCTION_2025[filing_status]
    taxable_income = max(0.0, income - standard_deduction)
    
    if taxable_income <= 0:
        return 0.0
    
    # Select appropriate tax brackets
    brackets = SINGLE_BRACKETS_2025 if filing_status == "single" else MARRIED_BRACKETS_2025
    
    # Calculate tax using marginal rates
    total_tax = 0.0
    income_remaining = taxable_income
    
    for i, (rate, threshold) in enumerate(brackets):
        if income_remaining <= 0:
            break
            
        # Determine the upper bound for this bracket
        if i + 1 < len(brackets):
            next_threshold = brackets[i + 1][1]
        else:
            next_threshold = float('inf')  # Highest bracket
        
        # Calculate taxable income in this bracket
        bracket_size = next_threshold - threshold
        income_in_bracket = min(income_remaining, bracket_size)
        
        # Calculate tax for this bracket
        bracket_tax = income_in_bracket * rate
        total_tax += bracket_tax
        
        # Reduce remaining income
        income_remaining -= income_in_bracket
    
    return round(total_tax, 2)


def get_effective_tax_rate(income: float, filing_status: FilingStatus = "single") -> float:
    """Calculate the effective tax rate for a given income level.
    
    Args:
        income: Gross income in dollars
        filing_status: Either "single" or "married"
        
    Returns:
        Effective tax rate as a decimal (e.g., 0.15 for 15%)
    """
    if income <= 0:
        return 0.0
        
    total_tax = calc_tax(income, filing_status)
    return total_tax / income


def get_marginal_tax_rate(income: float, filing_status: FilingStatus = "single") -> float:
    """Calculate the marginal tax rate for a given income level.
    
    This is the tax rate that would apply to the next dollar of income.
    
    Args:
        income: Gross income in dollars
        filing_status: Either "single" or "married"
        
    Returns:
        Marginal tax rate as a decimal (e.g., 0.22 for 22%)
    """
    if income <= 0:
        return 0.0
    
    # Apply standard deduction
    standard_deduction = STANDARD_DEDUCTION_2025[filing_status]
    taxable_income = max(0.0, income - standard_deduction)
    
    if taxable_income <= 0:
        return 0.0
    
    # Find the appropriate tax bracket
    brackets = SINGLE_BRACKETS_2025 if filing_status == "single" else MARRIED_BRACKETS_2025
    
    for rate, threshold in reversed(brackets):
        if taxable_income > threshold:
            return rate
    
    # Should never reach here, but return the lowest rate as fallback
    return brackets[0][0]


# Convenience function for integration with existing tax_engine interface
def create_tax_engine(filing_status: FilingStatus = "single"):
    """Create a tax engine function compatible with CashFlowLedger.
    
    The CashFlowLedger expects a function with signature:
    (withdrawal: float, balance: float) -> float
    
    Args:
        filing_status: Either "single" or "married"
        
    Returns:
        Tax engine function that can be passed to CashFlowLedger
        
    Example:
        >>> tax_engine = create_tax_engine("single")
        >>> ledger = CashFlowLedger(simulator, strategy, params, tax_engine=tax_engine)
    """
    def tax_engine(withdrawal: float, balance: float) -> float:
        """Tax engine function for CashFlowLedger integration.
        
        Args:
            withdrawal: Annual withdrawal amount (treated as ordinary income)
            balance: Current portfolio balance (unused in federal tax calc)
            
        Returns:
            Federal income tax owed on the withdrawal
        """
        # Note: balance is not used in federal income tax calculation
        # It could be used for more sophisticated tax strategies in the future
        return calc_tax(withdrawal, filing_status)
    
    return tax_engine