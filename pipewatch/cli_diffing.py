"""CLI command for metric diffing."""
from __future__ import annotations

import click
from rich.console import Console

from pipewatch.diffing import diff_history, status_regressions
from pipewatch.display_diffing import render_diff_table, render_diff_summary
from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.collector import MetricCollector


@click.command("diff")
@click.option("--window", default=2, show_default=True,
              help="Number of steps back to compare against.")
@click.option("--regressions-only", is_flag=True, default=False,
              help="Show only metrics whose status worsened.")
def diff_cmd(window: int, regressions_only: bool) -> None:
    """Compare latest metric values against an earlier window."""
    console = Console()

    # Build a small demo history for standalone invocation
    history = MetricHistory()
    collector = MetricCollector()

    try:
        from pipewatch.cli import _load_rules  # type: ignore
        rules = _load_rules()
        for rule in rules:
            collector.add_rule(rule)
    except Exception:
        rules = []

    if not history.metric_names():
        console.print("[yellow]No history data available. Run 'pipewatch watch' first.[/yellow]")
        return

    diffs = diff_history(history, window=window)
    if regressions_only:
        diffs = status_regressions(diffs)

    if not diffs:
        console.print("[green]No diffs to display.[/green]")
        return

    render_diff_table(diffs, console=console)
    render_diff_summary(diffs, console=console)
