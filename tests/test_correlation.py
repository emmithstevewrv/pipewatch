"""Tests for pipewatch.correlation."""
import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.correlation import correlate, correlate_all, CorrelationResult


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="")


def make_history(*pairs: tuple) -> MetricHistory:
    """Helper to build a MetricHistory from (name, values) pairs.

    Example::

        h = make_history(("a", [1, 2, 3]), ("b", [4, 5, 6]))
    """
    h = MetricHistory()
    max_len = max(len(values) for _, values in pairs)
    for i in range(max_len):
        for name, values in pairs:
            if i < len(values):
                h.record(make_metric(name, values[i]))
    return h


@pytest.fixture
def history_with_two_metrics() -> MetricHistory:
    h = MetricHistory()
    for v in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
        h.record(make_metric("alpha", v))
        h.record(make_metric("beta", v * 2))  # perfect positive correlation
    return h


def test_returns_none_when_too_few_samples():
    h = MetricHistory()
    for v in [1.0, 2.0]:
        h.record(make_metric("a", v))
        h.record(make_metric("b", v))
    result = correlate(h, "a", "b", min_samples=5)
    assert result is None


def test_perfect_positive_correlation(history_with_two_metrics):
    r = correlate(history_with_two_metrics, "alpha", "beta")
    assert r is not None
    assert abs(r.coefficient - 1.0) < 1e-6
    assert r.metric_a == "alpha"
    assert r.metric_b == "beta"


def test_perfect_negative_correlation():
    h = make_history(("up", [1.0, 2.0, 3.0, 4.0, 5.0]), ("down", [5.0, 4.0, 3.0, 2.0, 1.0]))
    r = correlate(h, "up", "down")
    assert r is not None
    assert abs(r.coefficient - (-1.0)) < 1e-6


def test_sample_count_is_min_of_both(history_with_two_metrics):
    r = correlate(history_with_two_metrics, "alpha", "beta")
    assert r.sample_count == 6


def test_correlate_all_returns_pair(history_with_two_metrics):
    results = correlate_all(history_with_two_metrics)
    assert len(results) == 1
    assert isinstance(results[0], CorrelationResult)


def test_correlate_all_empty_when_insufficient():
    h = MetricHistory()
    for v in [1.0, 2.0]:
        h.record(make_metric("x", v))
        h.record(make_metric("y", v))
    results = correlate_all(h, min_samples=5)
    assert results == []


def test_str_representation(history_with_two_metrics):
    r = correlate(history_with_two_metrics, "alpha", "beta")
    s = str(r)
    assert "alpha" in s
    assert "beta" in s
    assert "strong" in s
    assert "positive" in s
