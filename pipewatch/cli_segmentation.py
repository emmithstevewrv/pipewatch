"""CLI command for metric segmentation."""

from __future__ import annotations

from datetime import timedelta

import click

from pipewatch.history import MetricHistory
from pipewatch.segmentation import segment_all
from pipewatch.display_segmentation import render_segment_table, render_segment_summary


@click.command("segment")
@click.option(
    "--window",
    default=60,
    show_default=True,
    help="Width of each time window in seconds.",
)
@click.option(
    "--count",
    default=5,
    show_default=True,
    help="Number of windows to produce per metric.",
)
@click.option(
    "--metric",
    default=None,
    help="Restrict output to a single named metric.",
)
@click.option(
    "--summary",
    is_flag=True,
    default=False,
    help="Show only the cross-metric summary table.",
)
@click.pass_context
def segment_cmd(ctx: click.Context, window: int, count: int, metric: str | None, summary: bool) -> None:
    """Segment metric history into equal time windows and compare means."""
    history: MetricHistory = ctx.obj.get("history") if ctx.obj else MetricHistory()

    window_td = timedelta(seconds=window)
    all_segs = segment_all(history, window_size=window_td, num_windows=count)

    if not all_segs:
        click.echo("No metric history available for segmentation.")
        return

    if summary:
        render_segment_summary(all_segs)
        return

    if metric:
        if metric not in all_segs:
            click.echo(f"Metric {metric!r} not found in history.")
            return
        render_segment_table(metric, all_segs[metric])
    else:
        for name, segs in all_segs.items():
            render_segment_table(name, segs)
