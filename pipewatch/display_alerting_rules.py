"""Rich display helpers for escalation rule results."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.alerting_rules import EscalationResult
from pipewatch.metrics import MetricStatus

_console = Console()


def _status_color(status: MetricStatus) -> str:
    return {
        MetricStatus.OK: "green",
        MetricStatus.WARNING: "yellow",
        MetricStatus.CRITICAL: "red",
        MetricStatus.UNKNOWN: "dim",
    }.get(status, "white")


def render_escalation_table(results: List[EscalationResult]) -> None:
    """Render a Rich table of escalation evaluation results."""
    table = Table(
        title="Escalation Rule Evaluation",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Consecutive", justify="right")
    table.add_column("Min Required", justify="right")
    table.add_column("Alert?", justify="center")

    for r in results:
        color = _status_color(r.current_status)
        alert_cell = "[bold red]YES[/]" if r.should_alert else "[dim]no[/]"
        table.add_row(
            r.metric_name,
            f"[{color}]{r.current_status.value}[/]",
            str(r.consecutive_count),
            str(r.rule.min_consecutive),
            alert_cell,
        )

    _console.print(table)


def render_escalation_summary(results: List[EscalationResult]) -> None:
    """Print a one-line summary of how many escalations are firing."""
    total = len(results)
    firing = sum(1 for r in results if r.should_alert)
    if total == 0:
        _console.print("[dim]No escalation rules evaluated.[/]")
        return
    _console.print(
        f"Escalation rules: [bold]{total}[/] evaluated — "
        f"[bold red]{firing}[/] firing, "
        f"[dim]{total - firing}[/] suppressed."
    )
