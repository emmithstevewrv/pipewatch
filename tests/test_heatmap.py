"""Tests for pipewatch.heatmap."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.heatmap import HeatmapRow, build_heatmap


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


def _add(history: MetricHistory, name: str, value: float, status: MetricStatus, hour: int) -> None:
    ts = datetime(2024, 1, 1, hour, 0, 0)
    history.record(make_metric(name, value, status), timestamp=ts)


@pytest.fixture()
def simple_history() -> MetricHistory:
    h = MetricHistory()
    _add(h, "rows", 10.0, MetricStatus.OK, hour=9)
    _add(h, "rows", 5.0, MetricStatus.WARNING, hour=3)
    _add(h, "rows", 1.0, MetricStatus.CRITICAL, hour=3)
    _add(h, "rows", 20.0, MetricStatus.OK, hour=3)
    return h


def test_build_heatmap_returns_one_row_per_metric(simple_history):
    rows = build_heatmap(simple_history)
    assert len(rows) == 1
    assert rows[0].metric_name == "rows"


def test_ok_snapshots_not_counted_as_incidents(simple_history):
    rows = build_heatmap(simple_history)
    row = rows[0]
    # hour 9 has one OK snapshot → 0 incidents
    assert row.counts[9] == 0
    assert row.totals[9] == 1


def test_warning_and_critical_counted(simple_history):
    rows = build_heatmap(simple_history)
    row = rows[0]
    # hour 3: 2 non-OK out of 3 total
    assert row.counts[3] == 2
    assert row.totals[3] == 3


def test_incident_rate_calculation(simple_history):
    row = build_heatmap(simple_history)[0]
    rate = row.incident_rate(3)
    assert rate == pytest.approx(2 / 3)


def test_incident_rate_none_for_empty_hour(simple_history):
    row = build_heatmap(simple_history)[0]
    assert row.incident_rate(0) is None


def test_peak_hour_identifies_worst_hour(simple_history):
    row = build_heatmap(simple_history)[0]
    # hour 3 has 2/3 rate; hour 9 has 0/1 rate
    assert row.peak_hour() == 3


def test_peak_hour_none_when_all_ok():
    h = MetricHistory()
    _add(h, "m", 1.0, MetricStatus.OK, hour=10)
    _add(h, "m", 2.0, MetricStatus.OK, hour=11)
    row = build_heatmap(h)[0]
    assert row.peak_hour() is None


def test_multiple_metrics_produce_multiple_rows():
    h = MetricHistory()
    _add(h, "alpha", 1.0, MetricStatus.OK, hour=0)
    _add(h, "beta", 2.0, MetricStatus.CRITICAL, hour=0)
    rows = build_heatmap(h)
    names = {r.metric_name for r in rows}
    assert names == {"alpha", "beta"}


def test_str_representation():
    row = HeatmapRow(metric_name="test_metric")
    s = str(row)
    assert "test_metric" in s
