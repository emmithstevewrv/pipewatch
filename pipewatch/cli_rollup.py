"""CLI command for displaying rollup summaries of metric history."""

from __future__ import annotations

import click

from pipewatch.history import MetricHistory
from pipewatch.rollup import rollup_all
from pipewatch.display_rollup import render_rollup_table, render_rollup_summary


@click.command("rollup")
@click.option(
    "--window",
    "-w",
    default=60,
    show_default=True,
    help="Window size in seconds to group snapshots into rollup buckets.",
)
@click.option(
    "--metric",
    "-m",
    multiple=True,
    help="Metric name(s) to include. Repeatable. Defaults to all metrics.",
)
@click.option(
    "--summary",
    "-s",
    is_flag=True,
    default=False,
    help="Show a brief summary instead of the full rollup table.",
)
@click.pass_context
def rollup_cmd(ctx: click.Context, window: int, metric: tuple[str, ...], summary: bool) -> None:
    """Display time-windowed rollup statistics for recorded metrics.

    Groups metric snapshots into fixed-size time windows and reports
    the dominant status, min, max, and average value per window.

    Examples:

    \b
        pipewatch rollup --window 120
        pipewatch rollup -m rows_processed -m error_rate -w 30
        pipewatch rollup --summary
    """
    history: MetricHistory | None = ctx.obj.get("history") if ctx.obj else None

    if history is None:
        raise click.UsageError(
            "No MetricHistory available in context. "
            "Ensure the CLI is initialised with a shared history object."
        )

    metric_names = list(metric) if metric else None
    entries = rollup_all(history, window_seconds=window, metric_names=metric_names)

    if not entries:
        click.echo("No rollup data available. Record some metrics first.")
        return

    if summary:
        render_rollup_summary(entries)
    else:
        render_rollup_table(entries)
