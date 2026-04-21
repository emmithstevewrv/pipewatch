"""Tests for pipewatch.deduplication."""

from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.deduplication import (
    DeduplicationPolicy,
    deduplicate_series,
    deduplicate_history,
)


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, message="ok")


def make_snapshot(name: str, value: float, ts: datetime) -> MetricSnapshot:
    return MetricSnapshot(metric=make_metric(name, value), recorded_at=ts)


BASE = datetime(2024, 1, 1, 12, 0, 0)


def test_empty_series_returns_empty():
    assert deduplicate_series([]) == []


def test_single_snapshot_returned_unchanged():
    snap = make_snapshot("cpu", 50.0, BASE)
    assert deduplicate_series([snap]) == [snap]


def test_no_duplicates_all_kept():
    snaps = [
        make_snapshot("cpu", 10.0, BASE),
        make_snapshot("cpu", 20.0, BASE + timedelta(seconds=10)),
        make_snapshot("cpu", 30.0, BASE + timedelta(seconds=20)),
    ]
    result = deduplicate_series(snaps)
    assert len(result) == 3


def test_exact_duplicates_within_window_removed():
    policy = DeduplicationPolicy(time_window=timedelta(seconds=60), value_tolerance=0.0)
    snaps = [
        make_snapshot("cpu", 42.0, BASE),
        make_snapshot("cpu", 42.0, BASE + timedelta(seconds=5)),
        make_snapshot("cpu", 42.0, BASE + timedelta(seconds=10)),
    ]
    result = deduplicate_series(snaps, policy)
    assert len(result) == 1
    assert result[0].metric.value == 42.0


def test_duplicate_outside_time_window_kept():
    policy = DeduplicationPolicy(time_window=timedelta(seconds=30), value_tolerance=0.0)
    snaps = [
        make_snapshot("cpu", 42.0, BASE),
        make_snapshot("cpu", 42.0, BASE + timedelta(seconds=60)),
    ]
    result = deduplicate_series(snaps, policy)
    assert len(result) == 2


def test_value_tolerance_applied():
    policy = DeduplicationPolicy(time_window=timedelta(seconds=60), value_tolerance=1.0)
    snaps = [
        make_snapshot("cpu", 50.0, BASE),
        make_snapshot("cpu", 50.5, BASE + timedelta(seconds=5)),
        make_snapshot("cpu", 52.0, BASE + timedelta(seconds=10)),
    ]
    result = deduplicate_series(snaps, policy)
    assert len(result) == 2
    assert result[0].metric.value == 50.0
    assert result[1].metric.value == 52.0


def test_deduplicate_history_all_metrics():
    history = MetricHistory()
    for i in range(3):
        ts = BASE + timedelta(seconds=i * 5)
        history.record(make_metric("cpu", 70.0), recorded_at=ts)
        history.record(make_metric("mem", 40.0), recorded_at=ts)

    policy = DeduplicationPolicy(time_window=timedelta(seconds=60), value_tolerance=0.0)
    result = deduplicate_history(history, policy)

    assert "cpu" in result
    assert "mem" in result
    assert len(result["cpu"]) == 1
    assert len(result["mem"]) == 1


def test_policy_str_includes_window_and_tolerance():
    policy = DeduplicationPolicy(time_window=timedelta(seconds=120), value_tolerance=2.5)
    s = str(policy)
    assert "120" in s
    assert "2.5" in s
