"""Rich display helpers for heatmap data."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.heatmap import HeatmapRow

_CONSOLE = Console()

# Compact hour labels shown as column headers
_HOUR_LABELS = [f"{h:02d}" for h in range(24)]


def _rate_cell(rate: float | None) -> str:
    if rate is None:
        return "[dim]-[/dim]"
    pct = rate * 100
    if pct == 0:
        return "[green]·[/green]"
    if pct < 25:
        return f"[yellow]{pct:3.0f}%[/yellow]"
    if pct < 60:
        return f"[orange1]{pct:3.0f}%[/orange1]"
    return f"[red]{pct:3.0f}%[/red]"


def render_heatmap_table(rows: List[HeatmapRow], console: Console | None = None) -> None:
    con = console or _CONSOLE
    if not rows:
        con.print("[dim]No heatmap data available.[/dim]")
        return

    table = Table(title="Incident Rate Heatmap (by hour)", box=box.SIMPLE_HEAD, show_lines=False)
    table.add_column("Metric", style="bold", min_width=18)
    for label in _HOUR_LABELS:
        table.add_column(label, justify="right", min_width=4)

    for row in rows:
        cells = [_rate_cell(row.incident_rate(h)) for h in range(24)]
        table.add_row(row.metric_name, *cells)

    con.print(table)


def render_heatmap_summary(rows: List[HeatmapRow], console: Console | None = None) -> None:
    con = console or _CONSOLE
    if not rows:
        con.print("[dim]No heatmap summary available.[/dim]")
        return

    con.print("[bold]Peak Incident Hours[/bold]")
    for row in rows:
        peak = row.peak_hour()
        if peak is None:
            con.print(f"  {row.metric_name}: [dim]no data[/dim]")
        else:
            rate = row.incident_rate(peak) or 0
            con.print(f"  {row.metric_name}: hour [cyan]{peak:02d}[/cyan] ({rate*100:.0f}% incidents)")
