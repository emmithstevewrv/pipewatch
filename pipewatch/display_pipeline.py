"""Rich display helpers for pipeline health."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.pipeline import PipelineHealth

_console = Console()


def _score_color(score: float) -> str:
    if score >= 0.9:
        return "green"
    if score >= 0.6:
        return "yellow"
    return "red"


def render_pipeline_table(results: List[PipelineHealth], *, console: Console | None = None) -> None:
    """Render a table of per-pipeline health scores."""
    con = console or _console

    table = Table(title="Pipeline Health", box=box.SIMPLE_HEAVY, expand=False)
    table.add_column("Pipeline", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("OK", justify="right", style="green")
    table.add_column("Warning", justify="right", style="yellow")
    table.add_column("Critical", justify="right", style="red")
    table.add_column("Total", justify="right")

    if not results:
        con.print("[dim]No pipeline data available.[/dim]")
        return

    for r in results:
        color = _score_color(r.score)
        table.add_row(
            r.pipeline,
            f"[{color}]{r.score:.2f}[/{color}]",
            str(r.ok),
            str(r.warning),
            str(r.critical),
            str(r.total),
        )

    con.print(table)


def render_pipeline_summary(results: List[PipelineHealth], *, console: Console | None = None) -> None:
    """Print a one-line summary of overall fleet health."""
    con = console or _console

    if not results:
        con.print("[dim]No pipelines tracked.[/dim]")
        return

    degraded = [r for r in results if r.score < 0.9]
    if not degraded:
        con.print("[green]All pipelines healthy.[/green]")
    else:
        names = ", ".join(r.pipeline for r in degraded)
        con.print(f"[yellow]{len(degraded)} pipeline(s) degraded:[/yellow] {names}")
