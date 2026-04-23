"""Tests for pipewatch.display_partitioning."""

from __future__ import annotations

import io

from rich.console import Console

from pipewatch.partitioning import Partition
from pipewatch.display_partitioning import (
    render_partition_summary,
    render_partition_table,
)


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    con = Console(file=buf, highlight=False)
    fn(*args, console=con, **kwargs)
    return buf.getvalue()


def _make_partitions():
    low = Partition(label="low", low=0.0, high=33.0)
    high = Partition(label="high", low=66.0, high=100.0)
    from pipewatch.history import MetricHistory
    from pipewatch.metrics import Metric, MetricStatus

    h = MetricHistory()
    for v in [10.0, 70.0]:
        h.record(Metric(name="cpu", value=v, status=MetricStatus.OK, unit=""))

    from pipewatch.partitioning import partition_metric
    bounds = [("low", 0.0, 33.0), ("high", 66.0, 100.0)]
    return {"cpu": partition_metric(h, "cpu", bounds)}


def test_render_table_contains_metric_name() -> None:
    data = _make_partitions()
    out = _capture(render_partition_table, data)
    assert "cpu" in out


def test_render_table_shows_partition_labels() -> None:
    data = _make_partitions()
    out = _capture(render_partition_table, data)
    assert "low" in out
    assert "high" in out


def test_render_table_empty_data_shows_warning() -> None:
    out = _capture(render_partition_table, {})
    assert "No partition data" in out


def test_render_summary_shows_metric_count() -> None:
    data = _make_partitions()
    out = _capture(render_partition_summary, data)
    assert "1 metric" in out


def test_render_summary_shows_bucket_count() -> None:
    data = _make_partitions()
    out = _capture(render_partition_summary, data)
    assert "2 bucket" in out
