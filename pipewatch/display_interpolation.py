"""Rich-table rendering for interpolated metric series."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.interpolation import InterpolatedSeries

_console = Console()


def render_interpolation_table(
    series_list: List[InterpolatedSeries],
    console: Console | None = None,
    max_rows: int = 10,
) -> None:
    """Render a summary table of interpolated series."""
    con = console or _console

    if not series_list:
        con.print("[yellow]No interpolated series to display.[/yellow]")
        return

    table = Table(
        title="Interpolated Metric Series",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Points", justify="right")
    table.add_column("Filled", justify="right", style="yellow")
    table.add_column("Fill %", justify="right")
    table.add_column("First", style="dim")
    table.add_column("Last", style="dim")

    for s in series_list:
        filled = sum(s.interpolated_flags)
        pct = f"{100 * filled / len(s.values):.1f}" if s.values else "0.0"
        first_ts = s.timestamps[0].strftime("%H:%M:%S") if s.timestamps else "-"
        last_ts = s.timestamps[-1].strftime("%H:%M:%S") if s.timestamps else "-"
        table.add_row(
            s.metric_name,
            str(len(s.values)),
            str(filled),
            pct,
            first_ts,
            last_ts,
        )

    con.print(table)


def render_interpolation_summary(
    series_list: List[InterpolatedSeries],
    console: Console | None = None,
) -> None:
    """Print a one-line summary of all interpolation results."""
    con = console or _console
    if not series_list:
        con.print("[yellow]No series interpolated.[/yellow]")
        return

    total_points = sum(len(s.values) for s in series_list)
    total_filled = sum(sum(s.interpolated_flags) for s in series_list)
    con.print(
        f"[bold]Interpolation:[/bold] {len(series_list)} series, "
        f"{total_points} total points, "
        f"[yellow]{total_filled} synthesised[/yellow]."
    )
