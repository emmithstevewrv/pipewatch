"""Rich display helpers for outlier detection results."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.outlier import OutlierResult

_console = Console()


def _direction_style(direction: str) -> str:
    return {"high": "bold red", "low": "bold yellow", "none": "green"}.get(
        direction, "white"
    )


def render_outlier_table(results: List[OutlierResult], console: Console = _console) -> None:
    """Render a table of outlier results."""
    table = Table(
        title="Outlier Detection (IQR)",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Latest Value", justify="right")
    table.add_column("Lower Fence", justify="right")
    table.add_column("Upper Fence", justify="right")
    table.add_column("Outlier", justify="center")
    table.add_column("Direction", justify="center")

    for r in results:
        style = _direction_style(r.direction)
        table.add_row(
            r.metric_name,
            f"{r.value:.4f}",
            f"{r.lower_fence:.4f}",
            f"{r.upper_fence:.4f}",
            "[bold red]YES[/bold red]" if r.is_outlier else "[green]no[/green]",
            f"[{style}]{r.direction}[/{style}]",
        )

    if not results:
        console.print("[dim]No outlier data available (insufficient samples).[/dim]")
        return

    console.print(table)


def render_outlier_summary(results: List[OutlierResult], console: Console = _console) -> None:
    """Print a brief summary line for outlier detection."""
    total = len(results)
    flagged = sum(1 for r in results if r.is_outlier)
    high = sum(1 for r in results if r.direction == "high")
    low = sum(1 for r in results if r.direction == "low")

    console.print(
        f"[bold]Outlier summary:[/bold] {flagged}/{total} metrics flagged "
        f"([red]{high} high[/red], [yellow]{low} low[/yellow])"
    )
