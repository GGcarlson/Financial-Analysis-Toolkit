"""Summary statistics and reporting functionality."""

from pathlib import Path
from typing import Any

import pandas as pd
from rich.table import Table


def calculate_success_rate(df: pd.DataFrame) -> float:
    """
    Calculate the success rate of simulations.

    Success is defined as having a non-zero balance at the end of the simulation.

    Args:
        df: DataFrame with simulation results

    Returns:
        Success rate as a percentage (0.0 to 1.0)
    """
    final_year = df["year"].max()
    final_balances = df[df["year"] == final_year]["balance"]
    success_rate = (final_balances > 0).mean()
    return float(success_rate)


def calculate_percentiles(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Calculate 10th, 50th (median), and 90th percentiles for balances by year.

    Args:
        df: DataFrame with simulation results

    Returns:
        Dictionary with percentile DataFrames
    """
    yearly_percentiles = (
        df.groupby("year")["balance"].quantile([0.1, 0.5, 0.9]).unstack()
    )
    yearly_percentiles.columns = ["p10", "p50", "p90"]

    return {
        "yearly": yearly_percentiles,
        "final": yearly_percentiles.iloc[-1].to_dict(),
    }


def create_summary_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Create comprehensive summary statistics from simulation results.

    Args:
        df: DataFrame with simulation results

    Returns:
        Dictionary containing all summary statistics
    """
    success_rate = calculate_success_rate(df)
    percentiles = calculate_percentiles(df)

    # Calculate additional statistics
    yearly_stats = (
        df.groupby("year")
        .agg(
            {
                "balance": ["mean", "median", "std", "min", "max"],
                "withdrawal_nominal": ["mean", "median"],
                "inflation": ["mean"],
            }
        )
        .round(2)
    )

    # Flatten column names
    yearly_stats.columns = [f"{col[0]}_{col[1]}" for col in yearly_stats.columns]

    # Get final year stats
    final_year = df["year"].max()
    final_year_stats = yearly_stats.loc[final_year].to_dict()

    # Count depleted portfolios by year
    depletion_by_year = (
        df.groupby("year").apply(lambda x: (x["balance"] <= 0).sum()).to_dict()
    )

    return {
        "success_rate": success_rate,
        "percentiles": percentiles,
        "yearly_stats": yearly_stats,
        "final_year_stats": final_year_stats,
        "depletion_by_year": depletion_by_year,
        "total_paths": df["path"].nunique(),
        "total_years": df["year"].nunique(),
    }


def create_summary_report(
    df: pd.DataFrame, strategy: str, params: dict[str, Any]
) -> Table:
    """
    Create a Rich table with comprehensive summary statistics.

    Args:
        df: DataFrame with simulation results
        strategy: Name of the strategy used
        params: Simulation parameters

    Returns:
        Rich Table object with formatted statistics
    """
    stats = create_summary_statistics(df)

    # Create main summary table
    table = Table(title="Retirement Simulation Summary Report")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Metric", style="white")
    table.add_column("Value", style="green")

    # Simulation parameters
    table.add_row("Parameters", "Strategy", strategy)
    table.add_row("", "Initial Balance", f"${params.get('init_balance', 0):,.2f}")
    table.add_row("", "Equity Allocation", f"{params.get('equity_pct', 0):.1%}")
    table.add_row("", "Annual Fees", f"{params.get('fees_bps', 0)} bps")
    table.add_row("", "Years", str(stats["total_years"]))
    table.add_row("", "Simulation Paths", str(stats["total_paths"]))

    # Success metrics
    table.add_row("Success Metrics", "Success Rate", f"{stats['success_rate']:.1%}")
    table.add_row(
        "",
        "Failed Paths",
        str(stats["total_paths"] - int(stats["success_rate"] * stats["total_paths"])),
    )

    # Final year statistics
    final_stats = stats["final_year_stats"]
    table.add_row("Final Year", "Mean Balance", f"${final_stats['balance_mean']:,.2f}")
    table.add_row("", "Median Balance", f"${final_stats['balance_median']:,.2f}")
    table.add_row("", "Std Dev", f"${final_stats['balance_std']:,.2f}")
    table.add_row("", "Min Balance", f"${final_stats['balance_min']:,.2f}")
    table.add_row("", "Max Balance", f"${final_stats['balance_max']:,.2f}")

    # Percentiles
    percentiles = stats["percentiles"]["final"]
    table.add_row("Percentiles", "10th Percentile", f"${percentiles['p10']:,.2f}")
    table.add_row("", "50th Percentile", f"${percentiles['p50']:,.2f}")
    table.add_row("", "90th Percentile", f"${percentiles['p90']:,.2f}")

    # Withdrawal statistics
    table.add_row(
        "Withdrawals",
        "Mean (Final Year)",
        f"${final_stats['withdrawal_nominal_mean']:,.2f}",
    )
    table.add_row(
        "", "Median (Final Year)", f"${final_stats['withdrawal_nominal_median']:,.2f}"
    )

    return table


def save_summary_csv(
    df: pd.DataFrame, stats: dict[str, Any], output_path: Path | str
) -> None:
    """
    Save detailed summary statistics to CSV file.

    Args:
        df: DataFrame with simulation results
        stats: Summary statistics dictionary
        output_path: Path where to save the CSV file
    """
    output_path = Path(output_path)

    # Create summary DataFrame
    summary_data = []

    # Add overall metrics
    summary_data.append(
        {
            "metric_type": "overall",
            "metric_name": "success_rate",
            "value": stats["success_rate"],
        }
    )
    summary_data.append(
        {
            "metric_type": "overall",
            "metric_name": "total_paths",
            "value": stats["total_paths"],
        }
    )
    summary_data.append(
        {
            "metric_type": "overall",
            "metric_name": "total_years",
            "value": stats["total_years"],
        }
    )

    # Add yearly percentiles
    yearly_percentiles = stats["percentiles"]["yearly"]
    for year in yearly_percentiles.index:
        for percentile in ["p10", "p50", "p90"]:
            summary_data.append(
                {
                    "metric_type": "yearly_percentile",
                    "metric_name": f"year_{year}_{percentile}",
                    "value": yearly_percentiles.loc[year, percentile],
                }
            )

    # Add yearly statistics
    yearly_stats = stats["yearly_stats"]
    for year in yearly_stats.index:
        for col in yearly_stats.columns:
            summary_data.append(
                {
                    "metric_type": "yearly_stat",
                    "metric_name": f"year_{year}_{col}",
                    "value": yearly_stats.loc[year, col],
                }
            )

    # Add depletion counts
    for year, count in stats["depletion_by_year"].items():
        summary_data.append(
            {
                "metric_type": "depletion",
                "metric_name": f"year_{year}_depleted",
                "value": count,
            }
        )

    # Convert to DataFrame and save
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_path, index=False)
