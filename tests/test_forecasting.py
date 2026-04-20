"""Tests for pipewatch.forecasting."""

from __future__ import annotations

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.forecasting import (
    ForecastResult,
    _linear_regression,
    forecast_metric,
    forecast_all,
)


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="units")


@pytest.fixture()
def history_with_linear_data() -> MetricHistory:
    """History where 'throughput' increases linearly: 10, 20, 30, 40, 50."""
    h = MetricHistory()
    for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
        h.record(make_metric("throughput", v))
    return h


def test_linear_regression_perfect_line():
    values = [2.0, 4.0, 6.0, 8.0, 10.0]
    slope, intercept = _linear_regression(values)
    assert abs(slope - 2.0) < 1e-9
    assert abs(intercept - 2.0) < 1e-9


def test_linear_regression_flat_line():
    values = [5.0, 5.0, 5.0, 5.0, 5.0]
    slope, intercept = _linear_regression(values)
    assert abs(slope) < 1e-9
    assert abs(intercept - 5.0) < 1e-9


def test_returns_none_when_too_few_samples():
    h = MetricHistory()
    for v in [1.0, 2.0]:
        h.record(make_metric("cpu", v))
    result = forecast_metric(h, make_metric("cpu", 0), horizon=1, min_samples=5)
    assert result is None


def test_forecast_predicted_value(history_with_linear_data):
    result = forecast_metric(
        history_with_linear_data, make_metric("throughput", 0), horizon=1
    )
    assert result is not None
    # next step after index 4 is index 5 => slope*5 + intercept = 10*5+10 = 60
    assert abs(result.predicted_value - 60.0) < 1e-6


def test_forecast_horizon_two(history_with_linear_data):
    result = forecast_metric(
        history_with_linear_data, make_metric("throughput", 0), horizon=2
    )
    assert result is not None
    assert abs(result.predicted_value - 70.0) < 1e-6


def test_forecast_result_fields(history_with_linear_data):
    result = forecast_metric(
        history_with_linear_data, make_metric("throughput", 0), horizon=1
    )
    assert result is not None
    assert result.metric_name == "throughput"
    assert result.horizon == 1
    assert result.sample_count == 5
    assert result.slope > 0


def test_forecast_all_returns_results(history_with_linear_data):
    results = forecast_all(history_with_linear_data, horizon=1, min_samples=5)
    assert len(results) == 1
    assert results[0].metric_name == "throughput"


def test_forecast_all_empty_history():
    h = MetricHistory()
    results = forecast_all(h, horizon=1, min_samples=5)
    assert results == []


def test_str_representation(history_with_linear_data):
    result = forecast_metric(
        history_with_linear_data, make_metric("throughput", 0), horizon=1
    )
    assert result is not None
    s = str(result)
    assert "throughput" in s
    assert "rising" in s
