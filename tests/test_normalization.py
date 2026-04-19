"""Tests for pipewatch.normalization."""

import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.normalization import normalize_metric, normalize_all, _minmax, _zscore


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="")


@pytest.fixture()
def history_with_data() -> MetricHistory:
    h = MetricHistory()
    for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
        h.record(make_metric("latency", v))
    return h


def test_minmax_range():
    result = _minmax([10.0, 20.0, 30.0])
    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(1.0)


def test_minmax_constant_values():
    result = _minmax([5.0, 5.0, 5.0])
    assert all(v == 0.0 for v in result)


def test_zscore_mean_zero():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _zscore(values)
    assert sum(result) == pytest.approx(0.0, abs=1e-9)


def test_zscore_constant_values():
    result = _zscore([7.0, 7.0, 7.0])
    assert all(v == 0.0 for v in result)


def test_normalize_metric_minmax(history_with_data):
    result = normalize_metric(history_with_data, "latency", method="minmax")
    assert result is not None
    assert result.method == "minmax"
    assert len(result.values) == 5
    assert result.values[0] == pytest.approx(0.0)
    assert result.values[-1] == pytest.approx(1.0)


def test_normalize_metric_zscore(history_with_data):
    result = normalize_metric(history_with_data, "latency", method="zscore")
    assert result is not None
    assert result.method == "zscore"
    assert sum(result.values) == pytest.approx(0.0, abs=1e-9)


def test_normalize_metric_too_few_samples():
    h = MetricHistory()
    h.record(make_metric("latency", 1.0))
    result = normalize_metric(h, "latency", min_samples=2)
    assert result is None


def test_normalize_metric_unknown_returns_none(history_with_data):
    result = normalize_metric(history_with_data, "unknown")
    assert result is None


def test_normalize_all_returns_all_metrics():
    h = MetricHistory()
    for name in ("cpu", "mem"):
        for v in [1.0, 2.0, 3.0]:
            h.record(make_metric(name, v))
    results = normalize_all(h)
    assert set(results.keys()) == {"cpu", "mem"}


def test_str_representation(history_with_data):
    result = normalize_metric(history_with_data, "latency")
    assert "latency" in str(result)
    assert "minmax" in str(result)
