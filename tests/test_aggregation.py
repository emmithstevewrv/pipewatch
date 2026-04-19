"""Tests for pipewatch.aggregation."""
from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.aggregation import aggregate_window, aggregate_all


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="ms")


@pytest.fixture
def populated_history():
    h = MetricHistory()
    now = datetime.utcnow()
    for i, v in enumerate([10.0, 20.0, 30.0]):
        m = make_metric("latency", v)
        with patch("pipewatch.history.datetime") as mock_dt:
            mock_dt.utcnow.return_value = now - timedelta(seconds=30 - i)
            h.record(m)
    return h


def test_returns_none_for_unknown_metric():
    h = MetricHistory()
    result = aggregate_window(h, "nonexistent", window_seconds=60)
    assert result is None


def test_aggregate_window_basic(populated_history):
    result = aggregate_window(populated_history, "latency", window_seconds=60)
    assert result is not None
    assert result.metric_name == "latency"
    assert result.count == 3
    assert result.min_value == pytest.approx(10.0)
    assert result.max_value == pytest.approx(30.0)
    assert result.avg_value == pytest.approx(20.0)


def test_aggregate_window_excludes_old_snapshots():
    h = MetricHistory()
    now = datetime.utcnow()
    old = make_metric("latency", 999.0)
    recent = make_metric("latency", 5.0)
    with patch("pipewatch.history.datetime") as mock_dt:
        mock_dt.utcnow.return_value = now - timedelta(seconds=120)
        h.record(old)
    with patch("pipewatch.history.datetime") as mock_dt:
        mock_dt.utcnow.return_value = now - timedelta(seconds=10)
        h.record(recent)
    result = aggregate_window(h, "latency", window_seconds=60)
    assert result is not None
    assert result.count == 1
    assert result.avg_value == pytest.approx(5.0)


def test_aggregate_all_returns_all_metrics(populated_history):
    m2 = make_metric("errors", 3.0)
    populated_history.record(m2)
    results = aggregate_all(populated_history, window_seconds=60)
    names = {r.metric_name for r in results}
    assert "latency" in names
    assert "errors" in names


def test_str_representation(populated_history):
    result = aggregate_window(populated_history, "latency", window_seconds=60)
    assert "latency" in str(result)
    assert "60s window" in str(result)
