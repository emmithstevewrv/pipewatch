"""Rich display helpers for sliding-window statistics."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from pipewatch.windowing import WindowStats

_console = Console()


def render_window_table(stats: List[WindowStats], window_seconds: float) -> None:
    """Print a table of window statistics to stdout."""
    table = Table(
        title=f"Sliding Window Stats  (last {window_seconds:.0f}s)",
        show_lines=False,
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Samples", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")

    for s in stats:
        table.add_row(
            s.metric_name,
            str(s.sample_count),
            f"{s.mean:.3f}" if s.mean is not None else "-",
            f"{s.std_dev:.3f}" if s.std_dev is not None else "-",
            f"{s.min_value:.3f}" if s.min_value is not None else "-",
            f"{s.max_value:.3f}" if s.max_value is not None else "-",
        )

    _console.print(table)


def render_window_summary(stats: List[WindowStats]) -> None:
    """Print a one-line summary of window computation results."""
    total = len(stats)
    with_data = sum(1 for s in stats if s.sample_count > 0)
    empty = total - with_data

    _console.print(
        f"[bold]Window summary:[/bold] "
        f"{total} metric(s) evaluated — "
        f"[green]{with_data} with data[/green], "
        f"[yellow]{empty} empty[/yellow]"
    )
