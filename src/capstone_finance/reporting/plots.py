"""Visualization functions for simulation results."""

from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# Use non-interactive backend for headless environments
matplotlib.use("Agg")


def create_equity_curve_plot(
    df: pd.DataFrame,
    output_path: Path | str,
    title: str | None = None,
    params: dict[str, Any] | None = None,
) -> None:
    """
    Create and save a plot showing the median equity curve over time.

    Args:
        df: DataFrame with simulation results
        output_path: Path where to save the PNG file
        title: Optional custom title for the plot
        params: Optional simulation parameters for annotations
    """
    # Calculate percentiles by year
    yearly_stats = df.groupby("year")["balance"].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    yearly_stats = yearly_stats.unstack()

    # Create figure with proper size and DPI
    plt.figure(figsize=(10, 6), dpi=100)

    # Plot median line
    plt.plot(
        yearly_stats.index.get_level_values(0),
        yearly_stats[0.5],
        "b-",
        linewidth=2,
        label="Median Balance",
    )

    # Add percentile bands
    years = yearly_stats.index.get_level_values(0)

    # 25th-75th percentile band
    plt.fill_between(
        years,
        yearly_stats[0.25],
        yearly_stats[0.75],
        alpha=0.3,
        color="blue",
        label="25th-75th Percentile",
    )

    # 10th-90th percentile band
    plt.fill_between(
        years,
        yearly_stats[0.1],
        yearly_stats[0.9],
        alpha=0.15,
        color="blue",
        label="10th-90th Percentile",
    )

    # Formatting
    if title:
        plt.title(title, fontsize=14, fontweight="bold")
    else:
        plt.title("Portfolio Balance Over Time", fontsize=14, fontweight="bold")

    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Portfolio Balance ($)", fontsize=12)

    # Format y-axis as currency
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    # Add grid
    plt.grid(True, alpha=0.3, linestyle="--")

    # Add legend
    plt.legend(loc="best", framealpha=0.9)

    # Add annotation with parameters if provided
    if params:
        annotation_text = (
            f"Initial Balance: ${params.get('init_balance', 0):,.0f}\n"
            f"Equity Allocation: {params.get('equity_pct', 0):.1%}\n"
            f"Strategy: {params.get('strategy', 'N/A')}"
        )
        plt.text(
            0.02,
            0.98,
            annotation_text,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.8},
            fontsize=9,
        )

    # Add zero line for reference
    plt.axhline(y=0, color="red", linestyle="--", alpha=0.5, linewidth=1)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot
    output_path = Path(output_path)
    plt.savefig(output_path, bbox_inches="tight", dpi=100)
    plt.close()


def create_withdrawal_plot(
    df: pd.DataFrame, output_path: Path | str, title: str | None = None
) -> None:
    """
    Create and save a plot showing withdrawal amounts over time.

    Args:
        df: DataFrame with simulation results
        output_path: Path where to save the PNG file
        title: Optional custom title for the plot
    """
    # Calculate withdrawal statistics by year
    yearly_withdrawals = df.groupby("year")["withdrawal_nominal"].quantile(
        [0.1, 0.5, 0.9]
    )
    yearly_withdrawals = yearly_withdrawals.unstack()

    # Create figure
    plt.figure(figsize=(10, 6), dpi=100)

    # Plot median withdrawal
    years = yearly_withdrawals.index.get_level_values(0)
    plt.plot(
        years,
        yearly_withdrawals[0.5],
        "g-",
        linewidth=2,
        label="Median Withdrawal",
    )

    # Add percentile band
    plt.fill_between(
        years,
        yearly_withdrawals[0.1],
        yearly_withdrawals[0.9],
        alpha=0.3,
        color="green",
        label="10th-90th Percentile",
    )

    # Formatting
    if title:
        plt.title(title, fontsize=14, fontweight="bold")
    else:
        plt.title("Annual Withdrawal Amounts", fontsize=14, fontweight="bold")

    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Withdrawal Amount ($)", fontsize=12)

    # Format y-axis as currency
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    # Add grid
    plt.grid(True, alpha=0.3, linestyle="--")

    # Add legend
    plt.legend(loc="best", framealpha=0.9)

    # Adjust layout
    plt.tight_layout()

    # Save the plot
    output_path = Path(output_path)
    plt.savefig(output_path, bbox_inches="tight", dpi=100)
    plt.close()


def create_success_rate_by_year_plot(
    df: pd.DataFrame, output_path: Path | str, title: str | None = None
) -> None:
    """
    Create and save a plot showing portfolio survival rate by year.

    Args:
        df: DataFrame with simulation results
        output_path: Path where to save the PNG file
        title: Optional custom title for the plot
    """
    # Calculate survival rate by year
    survival_by_year = df.groupby("year").apply(lambda x: (x["balance"] > 0).mean())

    # Create figure
    plt.figure(figsize=(10, 6), dpi=100)

    # Plot survival rate
    plt.plot(
        survival_by_year.index,
        survival_by_year.values * 100,
        "r-",
        linewidth=2,
        marker="o",
        markersize=4,
    )

    # Formatting
    if title:
        plt.title(title, fontsize=14, fontweight="bold")
    else:
        plt.title("Portfolio Survival Rate by Year", fontsize=14, fontweight="bold")

    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Survival Rate (%)", fontsize=12)

    # Set y-axis limits
    plt.ylim(0, 105)

    # Add grid
    plt.grid(True, alpha=0.3, linestyle="--")

    # Add horizontal lines at key thresholds
    for threshold in [50, 75, 90, 95]:
        plt.axhline(
            y=threshold,
            color="gray",
            linestyle=":",
            alpha=0.5,
            label=f"{threshold}%" if threshold == 90 else None,
        )

    # Adjust layout
    plt.tight_layout()

    # Save the plot
    output_path = Path(output_path)
    plt.savefig(output_path, bbox_inches="tight", dpi=100)
    plt.close()
