"""Rich rendering for aggregation windows."""
from __future__ import annotations
from typing import List
from rich.table import Table
from rich.console import Console
from rich import box
from pipewatch.aggregation import AggregationWindow

_console = Console()


def render_aggregation_table(windows: List[AggregationWindow], window_seconds: int = 60) -> None:
    if not windows:
        _console.print("[dim]No aggregation data available.[/dim]")
        return

    table = Table(
        title=f"Metric Aggregation (last {window_seconds}s)",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Samples", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Avg", justify="right", style="bold")

    for w in windows:
        table.add_row(
            w.metric_name,
            str(w.count),
            f"{w.min_value:.3f}",
            f"{w.max_value:.3f}",
            f"{w.avg_value:.3f}",
        )

    _console.print(table)


def render_aggregation_summary(windows: List[AggregationWindow]) -> None:
    if not windows:
        return
    _console.print(f"[bold]Aggregated [cyan]{len(windows)}[/cyan] metric(s).[/bold]")
