"""CLI command: pipewatch heatmap."""
from __future__ import annotations

import click

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.heatmap import build_heatmap
from pipewatch.display_heatmap import render_heatmap_table, render_heatmap_summary

from datetime import datetime, timedelta
import math


def _demo_history() -> MetricHistory:
    """Produce synthetic history with hourly variation for demo purposes."""
    history = MetricHistory()
    base = datetime(2024, 6, 1, 0, 0, 0)
    for day in range(5):
        for hour in range(24):
            ts = base + timedelta(days=day, hours=hour)
            # Simulate higher error rate during hours 2-5 (batch window)
            if 2 <= hour <= 5:
                status = MetricStatus.CRITICAL if (day + hour) % 3 == 0 else MetricStatus.WARNING
            else:
                status = MetricStatus.OK
            value = 100.0 + 20 * math.sin(hour / 3.0)
            m = Metric(name="rows_processed", value=value, status=status)
            history.record(m, timestamp=ts)

            # Second metric: random-ish
            status2 = MetricStatus.WARNING if hour % 7 == 0 else MetricStatus.OK
            m2 = Metric(name="latency_ms", value=float(hour * 10), status=status2)
            history.record(m2, timestamp=ts)
    return history


@click.command("heatmap")
@click.option("--summary", is_flag=True, default=False, help="Show peak-hour summary instead of full table.")
def heatmap_cmd(summary: bool) -> None:
    """Display an incident-rate heatmap across hours of the day."""
    history = _demo_history()
    rows = build_heatmap(history)
    if summary:
        render_heatmap_summary(rows)
    else:
        render_heatmap_table(rows)
