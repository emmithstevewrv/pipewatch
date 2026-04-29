"""Display helpers for metric profiling results."""

from __future__ import annotations

from typing import Sequence

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.profiling import MetricProfile

_console = Console()


def _fmt(value: float | None, precision: int = 4) -> str:
    if value is None:
        return "[dim]n/a[/dim]"
    return f"{value:.{precision}f}"


def render_profile_table(profiles: Sequence[MetricProfile], *, console: Console | None = None) -> None:
    """Render a Rich table summarising each MetricProfile."""
    con = console or _console

    table = Table(
        title="Metric Profiles",
        box=box.SIMPLE_HEAD,
        show_lines=False,
        highlight=True,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Samples", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("p50", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("p99", justify="right")

    for p in profiles:
        table.add_row(
            p.metric_name,
            str(p.sample_count),
            _fmt(p.min_value),
            _fmt(p.max_value),
            _fmt(p.mean),
            _fmt(p.std_dev),
            _fmt(p.p50),
            _fmt(p.p95),
            _fmt(p.p99),
        )

    con.print(table)


def render_profile_summary(profiles: Sequence[MetricProfile], *, console: Console | None = None) -> None:
    """Print a one-line summary of profiling results."""
    con = console or _console
    if not profiles:
        con.print("[yellow]No profiling data available.[/yellow]")
        return
    total_samples = sum(p.sample_count for p in profiles)
    con.print(
        f"[bold]Profiled[/bold] {len(profiles)} metric(s) "
        f"across [bold]{total_samples}[/bold] total sample(s)."
    )
