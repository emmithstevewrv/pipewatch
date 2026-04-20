"""Rich display helpers for forecast results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.forecasting import ForecastResult

console = Console()


def _trend_label(slope: float) -> str:
    if slope > 0.01:
        return "[green]↑ Rising[/green]"
    if slope < -0.01:
        return "[red]↓ Falling[/red]"
    return "[yellow]→ Flat[/yellow]"


def render_forecast_table(results: list[ForecastResult]) -> None:
    """Render a Rich table of forecast results."""
    table = Table(
        title="Metric Forecasts",
        box=box.ROUNDED,
        show_lines=False,
        highlight=True,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Horizon", justify="right")
    table.add_column("Predicted", justify="right")
    table.add_column("Slope", justify="right")
    table.add_column("Trend")
    table.add_column("Samples", justify="right")

    for r in results:
        table.add_row(
            r.metric_name,
            f"+{r.horizon}",
            f"{r.predicted_value:.4f}",
            f"{r.slope:.4f}",
            _trend_label(r.slope),
            str(r.sample_count),
        )

    console.print(table)


def render_forecast_summary(results: list[ForecastResult]) -> None:
    """Print a short textual summary of forecast results."""
    if not results:
        console.print("[dim]No forecast data available.[/dim]")
        return
    rising = sum(1 for r in results if r.slope > 0.01)
    falling = sum(1 for r in results if r.slope < -0.01)
    flat = len(results) - rising - falling
    console.print(
        f"Forecasts: [green]{rising} rising[/green], "
        f"[red]{falling} falling[/red], "
        f"[yellow]{flat} flat[/yellow] "
        f"across {len(results)} metric(s)."
    )
