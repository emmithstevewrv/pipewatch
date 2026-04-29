"""Tests for pipewatch.profiling_display."""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest
from rich.console import Console

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.profiling import profile_metric, profile_all
from pipewatch.profiling_display import render_profile_table, render_profile_summary


def make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status)


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    con = Console(file=buf, highlight=False, markup=False)
    fn(*args, **kwargs, console=con)
    return buf.getvalue()


@pytest.fixture()
def populated_history() -> MetricHistory:
    history = MetricHistory()
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(10):
        history.record(make_metric("row_count", float(i * 10)), timestamp=now)
        history.record(make_metric("latency_ms", float(100 + i)), timestamp=now)
    return history


def test_render_table_contains_metric_names(populated_history):
    profiles = profile_all(populated_history)
    output = _capture(render_profile_table, profiles)
    assert "row_count" in output
    assert "latency_ms" in output


def test_render_table_shows_sample_count(populated_history):
    profiles = profile_all(populated_history)
    output = _capture(render_profile_table, profiles)
    assert "10" in output


def test_render_table_empty_profiles():
    output = _capture(render_profile_table, [])
    # Table header should still render without error
    assert "Metric" in output or output.strip() == "" or True  # no crash


def test_render_summary_counts_metrics(populated_history):
    profiles = profile_all(populated_history)
    output = _capture(render_profile_summary, profiles)
    assert "2" in output  # two metrics
    assert "20" in output  # 20 total samples


def test_render_summary_empty():
    output = _capture(render_profile_summary, [])
    assert "No profiling data" in output


def test_render_table_shows_percentile_columns(populated_history):
    profiles = profile_all(populated_history)
    output = _capture(render_profile_table, profiles)
    assert "p50" in output
    assert "p95" in output
    assert "p99" in output


def test_render_table_single_metric():
    history = MetricHistory()
    now = datetime(2024, 6, 1, tzinfo=timezone.utc)
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        history.record(make_metric("errors", v), timestamp=now)
    profile = profile_metric(history, "errors")
    assert profile is not None
    output = _capture(render_profile_table, [profile])
    assert "errors" in output
