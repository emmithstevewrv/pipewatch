"""Rich-based rendering for pipeline health reports."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.report import Report
from pipewatch.metrics import MetricStatus

_STATUS_STYLE: dict = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
    MetricStatus.UNKNOWN: "dim",
}


def render_report(report: Report, console: Console | None = None) -> None:
    """Print a summary report table to the console."""
    if console is None:
        console = Console()

    table = Table(title="Pipeline Health Report", box=box.ROUNDED, show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Samples", justify="right")
    table.add_column("Latest", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Trend", justify="right")
    table.add_column("Status")

    for s in report.summaries:
        style = _STATUS_STYLE.get(s.latest_status, "")
        trend_str = f"{s.trend:+.3f}" if s.trend is not None else "n/a"
        table.add_row(
            s.name,
            str(s.sample_count),
            f"{s.latest_value:.4g}" if s.latest_value is not None else "n/a",
            f"{s.min_value:.4g}" if s.min_value is not None else "n/a",
            f"{s.max_value:.4g}" if s.max_value is not None else "n/a",
            f"{s.avg_value:.4g}" if s.avg_value is not None else "n/a",
            trend_str,
            f"[{style}]{s.latest_status.value}[/{style}]",
        )

    console.print(table)
    console.print(
        f"[green]OK: {report.ok_count}[/green]  "
        f"[yellow]WARNING: {report.warning_count}[/yellow]  "
        f"[red]CRITICAL: {report.critical_count}[/red]"
    )
