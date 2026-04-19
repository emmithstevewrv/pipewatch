"""Tests for pipewatch.filter."""

from __future__ import annotations

import pytest
from datetime import datetime

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricSnapshot
from pipewatch.filter import (
    MetricFilter,
    apply_filter,
    filter_by_status,
    filter_by_name,
)


def make_snapshot(name: str, value: float, status: MetricStatus) -> MetricSnapshot:
    metric = Metric(name=name, value=value, status=status)
    return MetricSnapshot(metric=metric, timestamp=datetime.utcnow())


@pytest.fixture()
def snapshots():
    return [
        make_snapshot("rows_loaded", 500.0, MetricStatus.OK),
        make_snapshot("rows_loaded", 80.0, MetricStatus.WARNING),
        make_snapshot("latency", 2.5, MetricStatus.OK),
        make_snapshot("latency", 9.9, MetricStatus.CRITICAL),
        make_snapshot("error_rate", 0.01, MetricStatus.OK),
    ]


def test_filter_by_name(snapshots):
    result = filter_by_name(snapshots, "latency")
    assert len(result) == 2
    assert all(s.metric.name == "latency" for s in result)


def test_filter_by_status_ok(snapshots):
    result = filter_by_status(snapshots, MetricStatus.OK)
    assert len(result) == 3


def test_filter_by_status_critical(snapshots):
    result = filter_by_status(snapshots, MetricStatus.CRITICAL)
    assert len(result) == 1
    assert result[0].metric.name == "latency"


def test_filter_by_min_value(snapshots):
    f = MetricFilter(min_value=100.0)
    result = apply_filter(snapshots, f)
    assert len(result) == 1
    assert result[0].metric.value == 500.0


def test_filter_by_max_value(snapshots):
    f = MetricFilter(max_value=1.0)
    result = apply_filter(snapshots, f)
    assert len(result) == 1
    assert result[0].metric.name == "error_rate"


def test_combined_filter(snapshots):
    f = MetricFilter(name="rows_loaded", status=MetricStatus.WARNING)
    result = apply_filter(snapshots, f)
    assert len(result) == 1
    assert result[0].metric.value == 80.0


def test_empty_snapshots():
    result = filter_by_name([], "rows_loaded")
    assert result == []


def test_no_criteria_matches_all(snapshots):
    result = apply_filter(snapshots, MetricFilter())
    assert len(result) == len(snapshots)
