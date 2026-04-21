"""Tests for pipewatch.display_diffing."""
from __future__ import annotations

import io

from rich.console import Console

from pipewatch.diffing import DiffEntry
from pipewatch.display_diffing import render_diff_table, render_diff_summary
from pipewatch.metrics import MetricStatus


def _make_entry(name: str, old: float, new: float,
                old_s: MetricStatus, new_s: MetricStatus) -> DiffEntry:
    return DiffEntry(
        metric_name=name,
        old_value=old,
        new_value=new,
        old_status=old_s,
        new_status=new_s,
    )


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    console = Console(file=buf, highlight=False, markup=False)
    fn(*args, console=console, **kwargs)
    return buf.getvalue()


def test_render_table_contains_metric_names():
    entries = [
        _make_entry("cpu", 10.0, 90.0, MetricStatus.OK, MetricStatus.CRITICAL),
        _make_entry("mem", 50.0, 55.0, MetricStatus.WARNING, MetricStatus.WARNING),
    ]
    output = _capture(render_diff_table, entries)
    assert "cpu" in output
    assert "mem" in output


def test_render_table_shows_delta():
    entries = [_make_entry("latency", 5.0, 15.0, MetricStatus.OK, MetricStatus.WARNING)]
    output = _capture(render_diff_table, entries)
    assert "+10" in output


def test_render_summary_regression_count():
    entries = [
        _make_entry("cpu", 10.0, 90.0, MetricStatus.OK, MetricStatus.CRITICAL),
        _make_entry("mem", 50.0, 55.0, MetricStatus.WARNING, MetricStatus.WARNING),
    ]
    output = _capture(render_diff_summary, entries)
    assert "1" in output
    assert "regression" in output


def test_render_summary_no_regressions():
    entries = [
        _make_entry("disk", 40.0, 38.0, MetricStatus.OK, MetricStatus.OK),
    ]
    output = _capture(render_diff_summary, entries)
    assert "0" in output
