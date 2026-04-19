"""Tests for pipewatch.anomaly module."""

import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.anomaly import detect_anomaly, detect_all_anomalies, AnomalyResult


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="ms")


@pytest.fixture
def history_with_stable_data():
    h = MetricHistory()
    for v in [10.0, 10.1, 9.9, 10.0, 10.2, 10.0]:
        h.record(make_metric("latency", v))
    return h


def test_returns_none_when_too_few_samples():
    h = MetricHistory()
    for v in [1.0, 2.0, 3.0]:
        h.record(make_metric("latency", v))
    result = detect_anomaly(h, "latency", min_samples=5)
    assert result is None


def test_no_anomaly_for_stable_data(history_with_stable_data):
    result = detect_anomaly(history_with_stable_data, "latency")
    assert result is not None
    assert result.is_anomaly is False


def test_anomaly_detected_for_spike():
    h = MetricHistory()
    for v in [10.0, 10.0, 10.0, 10.0, 10.0]:
        h.record(make_metric("latency", v))
    h.record(make_metric("latency", 999.0))
    result = detect_anomaly(h, "latency", threshold=2.5)
    assert result is not None
    assert result.is_anomaly is True
    assert result.value == 999.0


def test_returns_none_for_zero_stddev():
    h = MetricHistory()
    for _ in range(6):
        h.record(make_metric("latency", 5.0))
    result = detect_anomaly(h, "latency")
    assert result is None


def test_anomaly_result_str_contains_metric_name():
    h = MetricHistory()
    for v in [1.0, 1.0, 1.0, 1.0, 1.0]:
        h.record(make_metric("cpu", v))
    h.record(make_metric("cpu", 100.0))
    result = detect_anomaly(h, "cpu", threshold=2.0)
    assert result is not None
    assert "cpu" in str(result)
    assert "ANOMALY" in str(result)


def test_detect_all_anomalies_returns_only_anomalous():
    h = MetricHistory()
    for v in [10.0, 10.0, 10.0, 10.0, 10.0]:
        h.record(make_metric("stable", v))
        h.record(make_metric("spikey", v))
    h.record(make_metric("stable", 10.0))
    h.record(make_metric("spikey", 500.0))

    results = detect_all_anomalies(h, threshold=2.5)
    names = [r.metric_name for r in results]
    assert "spikey" in names
    assert "stable" not in names
