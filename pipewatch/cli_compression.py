"""CLI sub-command: compress — downsample metric history via LTTB."""
from __future__ import annotations

import click

from pipewatch.compression import compress_metric, compress_all
from pipewatch.display_compression import (
    render_compression_table,
    render_compression_summary,
)
from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricSnapshot
from datetime import datetime, timezone


def _demo_history() -> MetricHistory:
    """Build a small synthetic history for smoke-testing the CLI."""
    import math

    history = MetricHistory()
    now = datetime.now(tz=timezone.utc).timestamp()
    for i in range(120):
        value = 50 + 30 * math.sin(i / 10.0) + (i % 7) * 0.5
        m = Metric(name="demo.latency", value=value, status=MetricStatus.OK)
        snap = MetricSnapshot(metric=m, timestamp=now - (120 - i))
        history.record(snap)
    return history


@click.command("compress")
@click.option(
    "--metric",
    default=None,
    metavar="NAME",
    help="Compress a single named metric (default: all).",
)
@click.option(
    "--threshold",
    default=50,
    show_default=True,
    help="Target number of samples after compression.",
)
def compress_cmd(metric: str | None, threshold: int) -> None:
    """Downsample metric history using the LTTB algorithm."""
    history = _demo_history()

    if metric:
        result = compress_metric(history, metric, threshold=threshold)
        if result is None:
            click.echo(f"No data found for metric '{metric}'.")
            return
        results = [result]
    else:
        results = compress_all(history, threshold=threshold)

    render_compression_table(results)
    render_compression_summary(results)
