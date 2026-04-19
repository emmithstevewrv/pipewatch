"""Tests for pipewatch.retention."""

from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.retention import RetentionPolicy, apply_retention


def make_metric(name: str = "rows", value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _add_snapshot(history: MetricHistory, name: str, value: float, age_seconds: float):
    """Directly inject a snapshot with a controlled timestamp."""
    from pipewatch.history import MetricSnapshot
    from pipewatch.metrics import MetricStatus

    snap = MetricSnapshot(
        metric=make_metric(name, value),
        timestamp=datetime.utcnow() - timedelta(seconds=age_seconds),
    )
    history._data.setdefault(name, []).append(snap)


# ---------------------------------------------------------------------------


def test_no_policy_removes_nothing():
    h = MetricHistory()
    for i in range(5):
        h.record(make_metric("m", float(i)))
    policy = RetentionPolicy()
    removed = apply_retention(h, policy)
    assert removed == {}
    assert len(h.snapshots("m")) == 5


def test_max_samples_trims_oldest():
    h = MetricHistory()
    for i in range(10):
        h.record(make_metric("m", float(i)))
    policy = RetentionPolicy(max_samples=4)
    removed = apply_retention(h, policy)
    assert removed.get("m") == 6
    snaps = h.snapshots("m")
    assert len(snaps) == 4
    # newest values retained
    assert snaps[-1].metric.value == 9.0


def test_max_age_removes_old_snapshots():
    h = MetricHistory()
    _add_snapshot(h, "m", 1.0, age_seconds=200)
    _add_snapshot(h, "m", 2.0, age_seconds=100)
    _add_snapshot(h, "m", 3.0, age_seconds=10)
    policy = RetentionPolicy(max_age_seconds=60)
    removed = apply_retention(h, policy)
    assert removed.get("m") == 2
    assert len(h.snapshots("m")) == 1
    assert h.snapshots("m")[0].metric.value == 3.0


def test_combined_policy_applies_both_constraints():
    h = MetricHistory()
    _add_snapshot(h, "m", 1.0, age_seconds=500)
    for i in range(6):
        _add_snapshot(h, "m", float(10 + i), age_seconds=5)
    policy = RetentionPolicy(max_age_seconds=60, max_samples=3)
    apply_retention(h, policy)
    assert len(h.snapshots("m")) == 3


def test_multiple_metrics_pruned_independently():
    h = MetricHistory()
    for i in range(5):
        h.record(make_metric("a", float(i)))
    for i in range(3):
        h.record(make_metric("b", float(i)))
    policy = RetentionPolicy(max_samples=2)
    removed = apply_retention(h, policy)
    assert removed.get("a") == 3
    assert removed.get("b") == 1
