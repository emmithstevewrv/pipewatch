"""Rich display helpers for rollup results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.rollup import RollupEntry
from pipewatch.metrics import MetricStatus

_STATUS_COLOUR = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
}


def render_rollup_table(
    entries: list[RollupEntry],
    console: Console | None = None,
    window_seconds: float = 60.0,
) -> None:
    console = console or Console()

    table = Table(
        title=f"Metric Rollup  (window={window_seconds}s)",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Samples", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Status", justify="center")

    if not entries:
        console.print("[dim]No rollup data available.[/dim]")
        return

    for e in entries:
        colour = _STATUS_COLOUR.get(e.dominant_status, "white")
        table.add_row(
            e.metric_name,
            str(e.sample_count),
            f"{e.avg_value:.4f}",
            f"{e.min_value:.4f}",
            f"{e.max_value:.4f}",
            f"[{colour}]{e.dominant_status.value}[/{colour}]",
        )

    console.print(table)


def render_rollup_summary(
    entries: list[RollupEntry],
    console: Console | None = None,
) -> None:
    console = console or Console()

    if not entries:
        console.print("[dim]No rollup entries to summarise.[/dim]")
        return

    critical = sum(1 for e in entries if e.dominant_status == MetricStatus.CRITICAL)
    warning = sum(1 for e in entries if e.dominant_status == MetricStatus.WARNING)
    ok = sum(1 for e in entries if e.dominant_status == MetricStatus.OK)

    console.print(
        f"Rollup summary — "
        f"[green]OK: {ok}[/green]  "
        f"[yellow]Warning: {warning}[/yellow]  "
        f"[red]Critical: {critical}[/red]  "
        f"(total metrics: {len(entries)})"
    )
