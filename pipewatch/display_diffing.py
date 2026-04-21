"""Rich display helpers for metric diffs."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.diffing import DiffEntry
from pipewatch.metrics import MetricStatus

_STATUS_COLOR = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
}mt_status(s: MetricStatus | None) -> str:
    if s is None:
        return "[dim]unknown[/dim]"
    colors, "white")
    return f"[{color}]{s.value}[/{color}]"


def _fmt_delta(delta: float | None) -> str:
    if delta is None:
        return "[dim]n/a[/dim]"
    color = "red" if delta > 0 else ("green" if delta < 0 else "dim")
    return f"[{color}]{delta:+.4g}[/{color}]"


def render_diff_table(diffs: list[DiffEntry], console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Metric Diff", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Metric", style="bold")
    table.add_column("Old Value", justify="right")
    table.add_column("New Value", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Old Status")
    table.add_column("New Status")

    for d in diffs:
        old_v = f"{d.old_value:.4g}" if d.old_value is not None else "n/a"
        new_v = f"{d.new_value:.4g}" if d.new_value is not None else "n/a"
        table.add_row(
            d.metric_name,
            old_v,
            new_v,
            _fmt_delta(d.value_delta),
            _fmt_status(d.old_status),
            _fmt_status(d.new_status),
        )
    console.print(table)


def render_diff_summary(diffs: list[DiffEntry], console: Console | None = None) -> None:
    console = console or Console()
    regressions = [d for d in diffs if d.status_changed and d.new_status in
                   (MetricStatus.WARNING, MetricStatus.CRITICAL)]
    console.print(f"[bold]Diff summary:[/bold] {len(diffs)} metric(s) compared, "
                  f"[yellow]{len(regressions)}[/yellow] regression(s) detected.")
