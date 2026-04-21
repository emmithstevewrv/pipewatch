"""Tests for pipewatch.display_segmentation."""

from __future__ import annotations

from datetime import datetime, timedelta
from io import StringIO

from rich.console import Console

from pipewatch.segmentation import Segment
from pipewatch.display_segmentation import render_segment_table, render_segment_summary


def _make_segment(label: str, values: list[float]) -> Segment:
    from pipewatch.metrics import Metric, MetricStatus
    from pipewatch.history import MetricSnapshot

    base = datetime(2024, 1, 1, 12, 0, 0)
    snapshots = [
        MetricSnapshot(
            metric=Metric(name="x", value=v, status=MetricStatus.OK, message="ok"),
            timestamp=base + timedelta(seconds=i),
        )
        for i, v in enumerate(values)
    ]
    return Segment(
        label=label,
        start=base,
        end=base + timedelta(seconds=len(values) * 10),
        snapshots=snapshots,
    )


def _capture(fn, *args, **kwargs) -> str:
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    fn(*args, console=console, **kwargs)
    return buf.getvalue()


def test_render_table_contains_metric_name():
    segs = [_make_segment("T-1", [1.0, 2.0]), _make_segment("current", [3.0])]
    out = _capture(render_segment_table, "latency", segs)
    assert "latency" in out


def test_render_table_shows_all_labels():
    segs = [_make_segment("T-2", []), _make_segment("T-1", [1.0]), _make_segment("current", [2.0])]
    out = _capture(render_segment_table, "cpu", segs)
    assert "T-2" in out
    assert "current" in out


def test_render_table_empty_segment_shows_dash():
    segs = [_make_segment("current", [])]
    out = _capture(render_segment_table, "mem", segs)
    assert "—" in out


def test_render_summary_empty():
    out = _capture(render_segment_summary, {})
    assert "No segmentation" in out


def test_render_summary_shows_metric_names():
    data = {
        "latency": [_make_segment("T-1", [1.0, 2.0]), _make_segment("current", [3.0])],
        "errors": [_make_segment("T-1", [0.0]), _make_segment("current", [1.0])],
    }
    out = _capture(render_segment_summary, data)
    assert "latency" in out
    assert "errors" in out
