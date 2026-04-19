"""Rich display helpers for baseline comparison results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.baseline import BaselineResult

console = Console()


def render_baseline_table(results: list[BaselineResult]) -> None:
    if not results:
        console.print("[dim]No baseline comparisons available.[/dim]")
        return

    table = Table(
        title="Baseline Comparison",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold")
    table.add_column("Actual", justify="right")
    table.add_column("Expected", justify="right")
    table.add_column("Deviation", justify="right")
    table.add_column("Tolerance", justify="right")
    table.add_column("Status", justify="center")

    for r in results:
        status_str = "[green]OK[/green]" if r.within_tolerance else "[red]DEVIATION[/red]"
        table.add_row(
            r.metric.name,
            f"{r.metric.value:.2f}",
            f"{r.entry.expected_value:.2f}",
            f"{r.deviation_pct:.1f}%",
            f"{r.entry.tolerance_pct:.1f}%",
            status_str,
        )

    console.print(table)


def render_baseline_summary(results: list[BaselineResult]) -> None:
    if not results:
        return
    deviations = [r for r in results if not r.within_tolerance]
    if deviations:
        console.print(f"[bold red]{len(deviations)} baseline deviation(s) detected:[/bold red]")
        for r in deviations:
            console.print(f"  • {r}")
    else:
        console.print("[bold green]All metrics within baseline tolerance.[/bold green]")
