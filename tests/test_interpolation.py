"""Tests for pipewatch.interpolation."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.interpolation import (
    InterpolatedSeries,
    _linear_fill,
    interpolate_metric,
    interpolate_all,
)


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="ms")


def _add(history: MetricHistory, name: str, value: float, ts: datetime) -> None:
    snap = MetricSnapshot(metric=make_metric(name, value), timestamp=ts)
    history._data.setdefault(name, []).append(snap)


@pytest.fixture()
def base_time() -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture()
def simple_history(base_time: datetime) -> MetricHistory:
    h = MetricHistory()
    _add(h, "latency", 100.0, base_time)
    _add(h, "latency", 200.0, base_time + timedelta(seconds=120))
    return h


# ---------------------------------------------------------------------------
# _linear_fill
# ---------------------------------------------------------------------------

def test_linear_fill_midpoint() -> None:
    val = _linear_fill(0.0, 0.0, 100.0, 100.0, 50.0)
    assert val == pytest.approx(50.0)


def test_linear_fill_equal_times_returns_v0() -> None:
    val = _linear_fill(5.0, 42.0, 5.0, 99.0, 5.0)
    assert val == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# interpolate_metric
# ---------------------------------------------------------------------------

def test_returns_none_when_fewer_than_two_snapshots() -> None:
    h = MetricHistory()
    _add(h, "x", 1.0, datetime(2024, 1, 1))
    assert interpolate_metric(h, "x", interval_seconds=60) is None


def test_returns_none_for_unknown_metric() -> None:
    h = MetricHistory()
    assert interpolate_metric(h, "ghost", interval_seconds=60) is None


def test_interpolated_series_has_correct_metric_name(
    simple_history: MetricHistory,
) -> None:
    result = interpolate_metric(simple_history, "latency", interval_seconds=60)
    assert result is not None
    assert result.metric_name == "latency"


def test_grid_points_span_full_range(
    simple_history: MetricHistory, base_time: datetime
) -> None:
    result = interpolate_metric(simple_history, "latency", interval_seconds=60)
    assert result is not None
    assert result.timestamps[0] == pytest.approx(base_time, abs=timedelta(seconds=1))
    assert result.timestamps[-1] >= base_time + timedelta(seconds=119)


def test_original_anchor_not_flagged_as_interpolated(
    simple_history: MetricHistory,
) -> None:
    result = interpolate_metric(simple_history, "latency", interval_seconds=60)
    assert result is not None
    # First point must be an original anchor
    assert result.interpolated_flags[0] is False


def test_midpoint_is_flagged_as_interpolated(
    simple_history: MetricHistory,
) -> None:
    result = interpolate_metric(simple_history, "latency", interval_seconds=60)
    assert result is not None
    # Grid at t=60s is between the two anchors — must be synthetic
    assert result.interpolated_flags[1] is True


def test_midpoint_value_is_linearly_interpolated(
    simple_history: MetricHistory,
) -> None:
    result = interpolate_metric(simple_history, "latency", interval_seconds=60)
    assert result is not None
    # Midpoint (60 s) should be ~150 (halfway between 100 and 200)
    assert result.values[1] == pytest.approx(150.0, abs=1.0)


# ---------------------------------------------------------------------------
# interpolate_all
# ---------------------------------------------------------------------------

def test_interpolate_all_returns_one_series_per_metric() -> None:
    h = MetricHistory()
    base = datetime(2024, 6, 1, 8, 0, 0)
    for name, val in [("cpu", 10.0), ("mem", 50.0)]:
        _add(h, name, val, base)
        _add(h, name, val + 10, base + timedelta(seconds=120))

    results = interpolate_all(h, interval_seconds=60)
    names = {r.metric_name for r in results}
    assert names == {"cpu", "mem"}


def test_interpolate_all_skips_metrics_with_single_snapshot() -> None:
    h = MetricHistory()
    base = datetime(2024, 6, 1)
    _add(h, "solo", 1.0, base)
    results = interpolate_all(h, interval_seconds=60)
    assert results == []
