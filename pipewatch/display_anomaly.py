"""Rich-based rendering for anomaly detection results."""

from typing import Sequence

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.anomaly import AnomalyResult

console = Console()


def render_anomaly_table(results: Sequence[AnomalyResult]) -> None:
    """Render a table of anomaly detection results to stdout."""
    if not results:
        console.print("[green]No anomalies detected.[/green]")
        return

    table = Table(
        title="Anomaly Detection Results",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )

    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Value", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("Z-Score", justify="right")
    table.add_column("Status", justify="center")

    for r in results:
        status = "[red]ANOMALY[/red]" if r.is_anomaly else "[green]OK[/green]"
        table.add_row(
            r.metric_name,
            f"{r.value:.3f}",
            f"{r.mean:.3f}",
            f"{r.stddev:.3f}",
            f"{r.z_score:.2f}",
            status,
        )

    console.print(table)


def render_anomaly_summary(results: Sequence[AnomalyResult]) -> None:
    """Print a one-line summary of anomaly scan results."""
    total = len(results)
    anomalous = sum(1 for r in results if r.is_anomaly)
    if anomalous == 0:
        console.print(f"[green]Scanned {total} metric(s) — no anomalies found.[/green]")
    else:
        console.print(
            f"[red]Scanned {total} metric(s) — {anomalous} anomaly(ies) detected.[/red]"
        )
