"""Tests for pipewatch.windowing."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.windowing import compute_all_windows, compute_window


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, message="ok")


def _add(history: MetricHistory, name: str, value: float, age_seconds: float) -> None:
    """Record a snapshot with a timestamp *age_seconds* in the past."""
    metric = make_metric(name, value)
    history.record(metric)
    # Patch the timestamp of the most-recently added snapshot.
    snap = history.snapshots(name)[-1]
    snap.timestamp = datetime.utcnow() - timedelta(seconds=age_seconds)


@pytest.fixture()
def history() -> MetricHistory:
    return MetricHistory()


def test_returns_none_for_unknown_metric(history: MetricHistory) -> None:
    result = compute_window(history, "ghost", 60.0)
    assert result is None


def test_sample_count_within_window(history: MetricHistory) -> None:
    _add(history, "cpu", 10.0, age_seconds=5)
    _add(history, "cpu", 20.0, age_seconds=10)
    _add(history, "cpu", 30.0, age_seconds=120)  # outside 60-s window

    result = compute_window(history, "cpu", 60.0)
    assert result is not None
    assert result.sample_count == 2


def test_mean_is_correct(history: MetricHistory) -> None:
    _add(history, "mem", 40.0, age_seconds=1)
    _add(history, "mem", 60.0, age_seconds=2)

    result = compute_window(history, "mem", 60.0)
    assert result is not None
    assert result.mean == pytest.approx(50.0)


def test_std_dev_none_for_single_sample(history: MetricHistory) -> None:
    _add(history, "disk", 99.0, age_seconds=1)

    result = compute_window(history, "disk", 60.0)
    assert result is not None
    assert result.std_dev is None


def test_min_max_values(history: MetricHistory) -> None:
    for v in [5.0, 15.0, 10.0]:
        _add(history, "lat", v, age_seconds=1)

    result = compute_window(history, "lat", 60.0)
    assert result is not None
    assert result.min_value == pytest.approx(5.0)
    assert result.max_value == pytest.approx(15.0)


def test_empty_window_returns_zero_samples(history: MetricHistory) -> None:
    _add(history, "rps", 100.0, age_seconds=300)  # outside 60-s window

    result = compute_window(history, "rps", 60.0)
    assert result is not None
    assert result.sample_count == 0
    assert result.mean is None


def test_compute_all_windows_covers_all_metrics(history: MetricHistory) -> None:
    _add(history, "a", 1.0, age_seconds=1)
    _add(history, "b", 2.0, age_seconds=1)

    results = compute_all_windows(history, 60.0)
    names = {r.metric_name for r in results}
    assert names == {"a", "b"}


def test_window_seconds_stored_on_result(history: MetricHistory) -> None:
    _add(history, "x", 7.0, age_seconds=1)
    result = compute_window(history, "x", 120.0)
    assert result is not None
    assert result.window_seconds == 120.0
