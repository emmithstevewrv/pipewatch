"""Tests for pipewatch.smoothing."""

import pytest
from datetime import datetime, timezone

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.smoothing import smooth_metric, smooth_all, _ema


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, timestamp=datetime.now(timezone.utc))


@pytest.fixture
def history_with_data() -> MetricHistory:
    h = MetricHistory()
    for v in [10.0, 20.0, 15.0, 25.0, 30.0]:
        h.record(make_metric("latency", v))
    return h


def test_ema_first_value_unchanged():
    result = _ema([5.0, 10.0, 15.0], alpha=0.5)
    assert result[0] == 5.0


def test_ema_length_matches_input():
    values = [1.0, 2.0, 3.0, 4.0]
    assert len(_ema(values, alpha=0.3)) == len(values)


def test_ema_empty_input():
    assert _ema([], alpha=0.5) == []


def test_smooth_metric_returns_none_for_single_value():
    h = MetricHistory()
    h.record(make_metric("x", 1.0))
    assert smooth_metric(h, "x") is None


def test_smooth_metric_returns_none_for_unknown():
    h = MetricHistory()
    assert smooth_metric(h, "nonexistent") is None


def test_smooth_metric_basic(history_with_data):
    result = smooth_metric(history_with_data, "latency", alpha=0.3)
    assert result is not None
    assert result.metric_name == "latency"
    assert len(result.smoothed) == 5
    assert result.smoothed[0] == 10.0


def test_smooth_metric_latest_is_float(history_with_data):
    result = smooth_metric(history_with_data, "latency", alpha=0.5)
    assert isinstance(result.latest(), float)


def test_smooth_metric_invalid_alpha(history_with_data):
    with pytest.raises(ValueError):
        smooth_metric(history_with_data, "latency", alpha=0.0)


def test_smooth_all_returns_all_metrics():
    h = MetricHistory()
    for name in ["a", "b"]:
        for v in [1.0, 2.0, 3.0]:
            h.record(make_metric(name, v))
    results = smooth_all(h, alpha=0.4)
    assert "a" in results and "b" in results


def test_smooth_all_skips_insufficient_data():
    h = MetricHistory()
    h.record(make_metric("solo", 5.0))
    for v in [1.0, 2.0, 3.0]:
        h.record(make_metric("multi", v))
    results = smooth_all(h)
    assert "solo" not in results
    assert "multi" in results


def test_str_representation(history_with_data):
    result = smooth_metric(history_with_data, "latency")
    assert "latency" in str(result)
    assert "alpha" in str(result)
