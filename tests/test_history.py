"""Tests for MetricHistory."""
import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory, MetricSnapshot


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, unit="count", status=MetricStatus.OK)


def test_record_and_latest():
    h = MetricHistory()
    h.record(make_metric("rows", 10.0))
    h.record(make_metric("rows", 20.0))
    snap = h.latest("rows")
    assert snap is not None
    assert snap.metric.value == 20.0


def test_latest_unknown_metric_returns_none():
    h = MetricHistory()
    assert h.latest("nonexistent") is None


def test_values_returns_all_recorded():
    h = MetricHistory()
    for v in [1.0, 2.0, 3.0]:
        h.record(make_metric("latency", v))
    assert h.values("latency") == [1.0, 2.0, 3.0]


def test_trend_positive_slope():
    h = MetricHistory()
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        h.record(make_metric("errors", v))
    slope = h.trend("errors")
    assert slope is not None
    assert slope == pytest.approx(1.0)


def test_trend_flat():
    h = MetricHistory()
    for _ in range(5):
        h.record(make_metric("errors", 7.0))
    assert h.trend("errors") == pytest.approx(0.0)


def test_trend_returns_none_for_single_value():
    h = MetricHistory()
    h.record(make_metric("errors", 5.0))
    assert h.trend("errors") is None


def test_maxlen_evicts_old_entries():
    h = MetricHistory(maxlen=3)
    for v in [1.0, 2.0, 3.0, 4.0]:
        h.record(make_metric("q", v))
    assert h.values("q") == [2.0, 3.0, 4.0]


def test_known_metrics():
    h = MetricHistory()
    h.record(make_metric("a", 1.0))
    h.record(make_metric("b", 2.0))
    assert set(h.known_metrics()) == {"a", "b"}
