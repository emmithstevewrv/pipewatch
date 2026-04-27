"""Rich display helpers for watermark entries."""
from __future__ import annotations

from typing import Sequence

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.watermark import WatermarkEntry
from pipewatch.metrics import MetricStatus

_console = Console()

_STATUS_COLOR: dict[MetricStatus, str] = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
    MetricStatus.UNKNOWN: "dim",
}


def _fmt(value: float, status: MetricStatus) -> str:
    color = _STATUS_COLOR.get(status, "white")
    return f"[{color}]{value:.4g}[/{color}]"


def render_watermark_table(
    entries: Sequence[WatermarkEntry],
    *,
    console: Console | None = None,
) -> None:
    con = console or _console
    table = Table(
        title="Metric Watermarks",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold")
    table.add_column("High", justify="right")
    table.add_column("Low", justify="right")
    table.add_column("Samples", justify="right")

    for entry in entries:
        table.add_row(
            entry.metric_name,
            _fmt(entry.high, entry.high_status),
            _fmt(entry.low, entry.low_status),
            str(entry.sample_count),
        )

    con.print(table)


def render_watermark_summary(
    entries: Sequence[WatermarkEntry],
    *,
    console: Console | None = None,
) -> None:
    con = console or _console
    if not entries:
        con.print("[dim]No watermark data available.[/dim]")
        return
    total = len(entries)
    con.print(f"[bold]Watermarks tracked for {total} metric(s).[/bold]")
