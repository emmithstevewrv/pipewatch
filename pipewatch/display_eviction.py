"""Rich display helpers for eviction results."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.eviction import EvictionResult

_console = Console()


def render_eviction_table(results: List[EvictionResult]) -> None:
    """Render a table summarising per-metric eviction activity."""
    table = Table(
        title="Eviction Report",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Evicted", justify="right", style="yellow")
    table.add_column("Remaining", justify="right", style="green")

    if not results:
        table.add_row("[dim]no data[/dim]", "-", "-")
    else:
        for r in results:
            evicted_str = str(r.evicted_count) if r.evicted_count > 0 else "[dim]0[/dim]"
            table.add_row(r.metric_name, evicted_str, str(r.remaining_count))

    _console.print(table)


def render_eviction_summary(results: List[EvictionResult]) -> None:
    """Print a one-line summary of total evictions."""
    total_evicted = sum(r.evicted_count for r in results)
    total_remaining = sum(r.remaining_count for r in results)
    metrics_affected = sum(1 for r in results if r.evicted_count > 0)

    if total_evicted == 0:
        _console.print(
            "[green]✔ No snapshots evicted — history within capacity.[/green]"
        )
    else:
        _console.print(
            f"[yellow]⚠ Evicted [bold]{total_evicted}[/bold] snapshot(s) across "
            f"[bold]{metrics_affected}[/bold] metric(s). "
            f"[bold]{total_remaining}[/bold] snapshot(s) remaining.[/yellow]"
        )
