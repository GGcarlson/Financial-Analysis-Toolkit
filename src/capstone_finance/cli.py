"""Command-line interface for the Financial Analysis Toolkit."""

import importlib.metadata
import sys
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core.ledger import CashFlowLedger
from .core.market import MarketSimulator
from .core.models import PortfolioParams, YearState
from .strategies.base import BaseStrategy

app = typer.Typer(
    name="finance-cli",
    help="Financial Analysis Toolkit - Monte Carlo retirement simulations",
    no_args_is_help=True,
)
console = Console()


def get_available_strategies() -> dict[str, type[BaseStrategy]]:
    """Discover available strategies from entry-points."""
    strategies = {}
    try:
        eps = importlib.metadata.entry_points(group="capstone_finance.strategies")
        for ep in eps:
            try:
                strategy_cls = ep.load()
                strategies[ep.name] = strategy_cls
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not load strategy '{ep.name}': {e}[/yellow]"
                )
    except Exception as e:
        console.print(f"[red]Error loading strategies: {e}[/red]")

    return strategies


def create_results_dataframe(simulation_results: list[list[YearState]]) -> pd.DataFrame:
    """Convert simulation results to pandas DataFrame for CSV export."""
    rows = []
    for path_idx, path in enumerate(simulation_results):
        for year_state in path:
            rows.append(
                {
                    "path": path_idx,
                    "year": year_state.year,
                    "age": year_state.age,
                    "balance": year_state.balance,
                    "inflation": year_state.inflation,
                    "withdrawal_nominal": year_state.withdrawal_nominal,
                }
            )

    return pd.DataFrame(rows)


def display_summary_statistics(df: pd.DataFrame) -> None:
    """Display summary statistics in a rich table."""
    # Calculate statistics per year
    yearly_stats = (
        df.groupby("year")
        .agg(
            {
                "balance": ["mean", "median", "std", "min", "max"],
                "withdrawal_nominal": ["mean", "median"],
            }
        )
        .round(2)
    )

    # Flatten column names
    yearly_stats.columns = [f"{col[0]}_{col[1]}" for col in yearly_stats.columns]

    # Display final year statistics
    final_year_stats = yearly_stats.iloc[-1]

    table = Table(title="Final Year Summary Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Mean Balance", f"${final_year_stats['balance_mean']:,.2f}")
    table.add_row("Median Balance", f"${final_year_stats['balance_median']:,.2f}")
    table.add_row("Std Dev Balance", f"${final_year_stats['balance_std']:,.2f}")
    table.add_row("Min Balance", f"${final_year_stats['balance_min']:,.2f}")
    table.add_row("Max Balance", f"${final_year_stats['balance_max']:,.2f}")
    table.add_row(
        "Mean Withdrawal", f"${final_year_stats['withdrawal_nominal_mean']:,.2f}"
    )
    table.add_row(
        "Median Withdrawal", f"${final_year_stats['withdrawal_nominal_median']:,.2f}"
    )

    # Success rate (non-zero balance)
    success_rate = (df[df["year"] == df["year"].max()]["balance"] > 0).mean()
    table.add_row("Success Rate", f"{success_rate:.1%}")

    console.print(table)


@app.command()
def retire(
    strategy: str = typer.Option(
        "four_percent_rule", "--strategy", help="Withdrawal strategy to use"
    ),
    years: int = typer.Option(30, "--years", help="Number of years to simulate"),
    paths: int = typer.Option(
        1000, "--paths", help="Number of simulation paths to run"
    ),
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility"),
    init_balance: float = typer.Option(
        1_000_000.0, "--init-balance", help="Initial portfolio balance"
    ),
    equity_pct: float = typer.Option(
        0.6, "--equity-pct", help="Equity allocation (0.0 to 1.0)"
    ),
    fees_bps: int = typer.Option(50, "--fees-bps", help="Annual fees in basis points"),
    market_mode: str = typer.Option(
        "lognormal",
        "--market-mode",
        help="Market simulation mode (lognormal or bootstrap)",
    ),
    output: str | None = typer.Option(None, "--output", help="Output CSV file path"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    percent: float = typer.Option(
        0.05, "--percent", help="Percentage for constant_pct strategy (0.0 to 1.0)"
    ),
    alpha: float = typer.Option(
        0.7,
        "--alpha",
        help="Alpha parameter for endowment strategy (weight for current portfolio)",
    ),
    beta: float = typer.Option(
        0.3,
        "--beta",
        help="Beta parameter for endowment strategy (weight for moving average)",
    ),
    window: int = typer.Option(
        3, "--window", help="Window size for endowment strategy moving average"
    ),
) -> None:
    """Run retirement simulation with specified parameters."""

    # Validate inputs
    if equity_pct < 0 or equity_pct > 1:
        console.print("[red]Error: Equity percentage must be between 0 and 1[/red]")
        raise typer.Exit(1)

    if years <= 0:
        console.print("[red]Error: Years must be positive[/red]")
        raise typer.Exit(1)

    if paths <= 0:
        console.print("[red]Error: Paths must be positive[/red]")
        raise typer.Exit(1)

    if market_mode not in ["lognormal", "bootstrap"]:
        console.print(
            "[red]Error: Market mode must be 'lognormal' or 'bootstrap'[/red]"
        )
        raise typer.Exit(1)

    if percent < 0 or percent > 1:
        console.print("[red]Error: Percent must be between 0 and 1[/red]")
        raise typer.Exit(1)

    if alpha < 0 or alpha > 1:
        console.print("[red]Error: Alpha must be between 0 and 1[/red]")
        raise typer.Exit(1)

    if beta < 0 or beta > 1:
        console.print("[red]Error: Beta must be between 0 and 1[/red]")
        raise typer.Exit(1)

    if abs(alpha + beta - 1.0) > 1e-10:
        console.print("[red]Error: Alpha + Beta must equal 1.0[/red]")
        raise typer.Exit(1)

    if window < 1:
        console.print("[red]Error: Window must be at least 1[/red]")
        raise typer.Exit(1)

    # Load available strategies
    strategies = get_available_strategies()

    if not strategies:
        console.print("[red]Error: No strategies available[/red]")
        raise typer.Exit(1)

    if strategy not in strategies:
        console.print(f"[red]Error: Strategy '{strategy}' not found[/red]")
        console.print("Available strategies:")
        for name in strategies:
            console.print(f"  - {name}")
        raise typer.Exit(1)

    # Initialize components
    if verbose:
        console.print("[blue]Initializing simulation components...[/blue]")

    params = PortfolioParams(
        init_balance=init_balance, equity_pct=equity_pct, fees_bps=fees_bps, seed=seed
    )

    market_simulator = MarketSimulator(params, mode=market_mode)

    # Create strategy instance with appropriate parameters
    if strategy == "constant_pct":
        strategy_instance = strategies[strategy](percentage=percent)
    elif strategy == "endowment":
        strategy_instance = strategies[strategy](alpha=alpha, beta=beta, window=window)
    else:
        strategy_instance = strategies[strategy]()

    ledger = CashFlowLedger(market_simulator, strategy_instance, params)

    # Run simulation
    console.print(
        f"[green]Running {paths} simulation paths for {years} years...[/green]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Simulating...", total=None)

        try:
            results = ledger.run(years=years, paths=paths)
            progress.update(task, description="Simulation complete!")
        except Exception as e:
            console.print(f"[red]Simulation failed: {e}[/red]")
            raise typer.Exit(1) from e

    # Convert to DataFrame
    if verbose:
        console.print("[blue]Processing results...[/blue]")

    df = create_results_dataframe(results)

    # Display summary
    console.print("\n[green]Simulation completed successfully![/green]")
    console.print(f"Strategy: {strategy}")
    console.print(f"Years: {years}")
    console.print(f"Paths: {paths}")
    console.print(f"Market Mode: {market_mode}")
    console.print(f"Initial Balance: ${init_balance:,.2f}")
    console.print(f"Equity Allocation: {equity_pct:.1%}")
    console.print(f"Annual Fees: {fees_bps} bps")

    display_summary_statistics(df)

    # Save to CSV if requested
    if output:
        output_path = Path(output)
        try:
            df.to_csv(output_path, index=False)
            console.print(f"\n[green]Results saved to: {output_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving CSV: {e}[/red]")
            raise typer.Exit(1) from e

    if verbose:
        console.print(f"\n[blue]Total data points: {len(df)}[/blue]")


@app.command()
def list_strategies() -> None:
    """List all available withdrawal strategies."""
    strategies = get_available_strategies()

    if not strategies:
        console.print("[yellow]No strategies found[/yellow]")
        return

    console.print("[green]Available withdrawal strategies:[/green]")
    for name, strategy_cls in strategies.items():
        doc = strategy_cls.__doc__ or "No description available"
        # Get first line of docstring
        first_line = doc.split("\n")[0].strip()
        console.print(f"  [cyan]{name}[/cyan]: {first_line}")


@app.command()
def version() -> None:
    """Show version information."""
    try:
        version = importlib.metadata.version("capstone_finance")
        console.print(f"Financial Analysis Toolkit v{version}")
    except importlib.metadata.PackageNotFoundError:
        console.print("Financial Analysis Toolkit (development version)")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
