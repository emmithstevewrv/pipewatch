"""Rich-based display helpers for metric output in the CLI."""
from typing import List

from rich.console import Console
from rich.table import Table

from pipewatch.metrics import Metric, MetricStatus

console = Console()

STATUS_STYLE = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "bold red",
    MetricStatus.UNKNOWN: "dim",
}


def render_metrics_table(metrics: List[Metric], title: str = "Pipeline Metrics") -> None:
    table = Table(title=title, show_lines=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Unit")
    table.add_column("Status", justify="center")
    table.add_column("Timestamp")

    for m in metrics:
        style = STATUS_STYLE.get(m.status, "")
        table.add_row(
            m.name,
            str(m.value),
            m.unit,
            f"[{style}]{m.status.value.upper()}[/{style}]",
            m.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        )
    console.print(table)


def render_alert_summary(metrics: List[Metric]) -> None:
    if not metrics:
        console.print("[green]All metrics within thresholds.[/green]")
        return
    console.print(f"[bold red]ALERT: {len(metrics)} critical metric(s) detected![/bold red]")
    for m in metrics:
        console.print(f"  • [red]{m.name}[/red] = {m.value} {m.unit}")
