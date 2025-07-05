"""Command-line interface for the Financial Analysis Toolkit."""

import importlib.metadata
import sys
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import ConfigModel
from .core.ledger import CashFlowLedger
from .core.market import MarketSimulator
from .core.models import PortfolioParams, YearState
from .reporting.plots import create_equity_curve_plot
from .reporting.summary import (
    create_summary_report,
    create_summary_statistics,
    save_summary_csv,
)
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
    # Configuration file
    config: str | None = typer.Option(
        None, "--config", help="Path to YAML configuration file"
    ),
    # Core simulation parameters
    strategy: str | None = typer.Option(
        None, "--strategy", help="Withdrawal strategy to use"
    ),
    years: int | None = typer.Option(
        None, "--years", help="Number of years to simulate"
    ),
    paths: int | None = typer.Option(
        None, "--paths", help="Number of simulation paths to run"
    ),
    seed: int | None = typer.Option(
        None, "--seed", help="Random seed for reproducibility"
    ),
    # Portfolio parameters
    init_balance: float | None = typer.Option(
        None, "--init-balance", help="Initial portfolio balance"
    ),
    equity_pct: float | None = typer.Option(
        None, "--equity-pct", help="Equity allocation (0.0 to 1.0)"
    ),
    fees_bps: int | None = typer.Option(
        None, "--fees-bps", help="Annual fees in basis points"
    ),
    # Market simulation parameters
    market_mode: str | None = typer.Option(
        None,
        "--market-mode",
        help="Market simulation mode (lognormal or bootstrap)",
    ),
    # Output parameters
    output: str | None = typer.Option(None, "--output", help="Output CSV file path"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    # Strategy-specific parameters
    percent: float | None = typer.Option(
        None, "--percent", help="Percentage for constant_pct strategy (0.0 to 1.0)"
    ),
    alpha: float | None = typer.Option(
        None,
        "--alpha",
        help="Alpha parameter for endowment strategy (weight for current portfolio)",
    ),
    beta: float | None = typer.Option(
        None,
        "--beta",
        help="Beta parameter for endowment strategy (weight for moving average)",
    ),
    window: int | None = typer.Option(
        None, "--window", help="Window size for endowment strategy moving average"
    ),
    # Guyton-Klinger strategy parameters
    initial_rate: float | None = typer.Option(
        None,
        "--initial-rate",
        help="Initial withdrawal rate for Guyton-Klinger strategy",
    ),
    guard_pct: float | None = typer.Option(
        None, "--guard-pct", help="Guardrail percentage for Guyton-Klinger strategy"
    ),
    raise_pct: float | None = typer.Option(
        None, "--raise-pct", help="Raise percentage for Guyton-Klinger strategy"
    ),
    cut_pct: float | None = typer.Option(
        None, "--cut-pct", help="Cut percentage for Guyton-Klinger strategy"
    ),
    # VPW strategy parameters
    vpw_table_path: str | None = typer.Option(
        None, "--vpw-table", help="Path to custom VPW table YAML file"
    ),
) -> None:
    """Run retirement simulation with specified parameters."""

    # Load configuration (defaults + config file + CLI args)
    try:
        if config:
            # Load from config file
            cfg = ConfigModel.from_yaml(config)
            if verbose:
                console.print(f"[blue]Loaded configuration from: {config}[/blue]")
        else:
            # Use defaults
            cfg = ConfigModel()

        # Merge CLI arguments (CLI args take precedence)
        cli_args = {
            "strategy": strategy,
            "years": years,
            "paths": paths,
            "seed": seed,
            "init_balance": init_balance,
            "equity_pct": equity_pct,
            "fees_bps": fees_bps,
            "market_mode": market_mode,
            "output": output,
            "verbose": verbose,
            "percent": percent,
            "alpha": alpha,
            "beta": beta,
            "window": window,
            "initial_rate": initial_rate,
            "guard_pct": guard_pct,
            "raise_pct": raise_pct,
            "cut_pct": cut_pct,
            "vpw_table_path": vpw_table_path,
        }

        # Merge config with CLI args (CLI takes precedence)
        final_config = cfg.merge_cli_args(**cli_args)

    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        raise typer.Exit(1) from e

    # Load available strategies
    strategies = get_available_strategies()

    if not strategies:
        console.print("[red]Error: No strategies available[/red]")
        raise typer.Exit(1)

    if final_config.strategy not in strategies:
        console.print(f"[red]Error: Strategy '{final_config.strategy}' not found[/red]")
        console.print("Available strategies:")
        for name in strategies:
            console.print(f"  - {name}")
        raise typer.Exit(1)

    # Initialize components
    if final_config.verbose:
        console.print("[blue]Initializing simulation components...[/blue]")

    params = PortfolioParams(
        init_balance=final_config.init_balance,
        equity_pct=final_config.equity_pct,
        fees_bps=final_config.fees_bps,
        seed=final_config.seed,
    )

    market_simulator = MarketSimulator(params, mode=final_config.market_mode)

    # Create strategy instance with appropriate parameters
    if final_config.strategy == "constant_pct":
        strategy_instance = strategies[final_config.strategy](
            percentage=final_config.percent
        )
    elif final_config.strategy == "endowment":
        strategy_instance = strategies[final_config.strategy](
            alpha=final_config.alpha, beta=final_config.beta, window=final_config.window
        )
    elif final_config.strategy == "guyton_klinger":
        strategy_instance = strategies[final_config.strategy](
            initial_rate=final_config.initial_rate,
            guard_pct=final_config.guard_pct,
            raise_pct=final_config.raise_pct,
            cut_pct=final_config.cut_pct,
        )
    elif final_config.strategy == "vpw":
        vpw_table_path = None
        if final_config.vpw_table_path:
            vpw_table_path = Path(final_config.vpw_table_path)
        strategy_instance = strategies[final_config.strategy](
            vpw_table_path=vpw_table_path
        )
    else:
        strategy_instance = strategies[final_config.strategy]()

    ledger = CashFlowLedger(market_simulator, strategy_instance, params)

    # Run simulation
    console.print(
        f"[green]Running {final_config.paths} simulation paths for {final_config.years} years...[/green]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Simulating...", total=None)

        try:
            results = ledger.run(years=final_config.years, paths=final_config.paths)
            progress.update(task, description="Simulation complete!")
        except Exception as e:
            console.print(f"[red]Simulation failed: {e}[/red]")
            raise typer.Exit(1) from e

    # Convert to DataFrame
    if final_config.verbose:
        console.print("[blue]Processing results...[/blue]")

    df = create_results_dataframe(results)

    # Display summary
    console.print("\n[green]Simulation completed successfully![/green]")
    console.print(f"Strategy: {final_config.strategy}")
    console.print(f"Years: {final_config.years}")
    console.print(f"Paths: {final_config.paths}")
    console.print(f"Market Mode: {final_config.market_mode}")
    console.print(f"Initial Balance: ${final_config.init_balance:,.2f}")
    console.print(f"Equity Allocation: {final_config.equity_pct:.1%}")
    console.print(f"Annual Fees: {final_config.fees_bps} bps")

    # Create enhanced summary report
    report_params = {
        "init_balance": final_config.init_balance,
        "equity_pct": final_config.equity_pct,
        "fees_bps": final_config.fees_bps,
        "strategy": final_config.strategy,
    }

    summary_table = create_summary_report(df, final_config.strategy, report_params)
    console.print("\n")
    console.print(summary_table)

    # Generate and save equity curve plot
    equity_curve_path = Path("equity_curve.png")
    if final_config.output:
        # Place equity curve in same directory as CSV output
        equity_curve_path = Path(final_config.output).parent / "equity_curve.png"

    try:
        create_equity_curve_plot(df, equity_curve_path, params=report_params)
        console.print(
            f"\n[green]Equity curve plot saved to: {equity_curve_path}[/green]"
        )
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not create equity curve plot: {e}[/yellow]"
        )

    # Save summary CSV
    summary_csv_path = Path("summary.csv")
    if final_config.output:
        # Place summary in same directory as main CSV output
        summary_csv_path = Path(final_config.output).parent / "summary.csv"

    try:
        stats = create_summary_statistics(df)
        save_summary_csv(df, stats, summary_csv_path)
        console.print(f"[green]Summary statistics saved to: {summary_csv_path}[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save summary CSV: {e}[/yellow]")

    # Save to CSV if requested
    if final_config.output:
        output_path = Path(final_config.output)
        try:
            df.to_csv(output_path, index=False)
            console.print(f"\n[green]Results saved to: {output_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving CSV: {e}[/red]")
            raise typer.Exit(1) from e

    if final_config.verbose:
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
