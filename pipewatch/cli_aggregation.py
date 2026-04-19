"""CLI sub-command: pipewatch aggregate — show windowed metric aggregations."""
from __future__ import annotations
import click
from pipewatch.history import MetricHistory
from pipewatch.aggregation import aggregate_all
from pipewatch.display_aggregation import render_aggregation_table, render_aggregation_summary


@click.command("aggregate")
@click.option(
    "--window",
    default=60,
    show_default=True,
    help="Aggregation window in seconds.",
    type=int,
)
@click.option(
    "--metric",
    default=None,
    help="Filter to a specific metric name.",
)
@click.pass_context
def aggregate_cmd(ctx: click.Context, window: int, metric: str | None) -> None:
    """Display time-window aggregations for recorded metrics."""
    history: MetricHistory = ctx.obj.get("history") if ctx.obj else None
    if history is None:
        click.echo("No history available. Run 'pipewatch watch' first.", err=True)
        raise SystemExit(1)

    windows = aggregate_all(history, window_seconds=window)

    if metric:
        windows = [w for w in windows if w.metric_name == metric]

    render_aggregation_table(windows, window_seconds=window)
    render_aggregation_summary(windows)
