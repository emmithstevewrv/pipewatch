"""Tests for pipewatch.rollup."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.rollup import rollup_metric, rollup_all, RollupEntry, _dominant_status


def make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status)


def _add_snapshot(
    history: MetricHistory,
    metric: Metric,
    age_seconds: float = 0.0,
) -> None:
    snap = MetricSnapshot(
        metric=metric,
        recorded_at=datetime.utcnow() - timedelta(seconds=age_seconds),
    )
    history._store.setdefault(metric.name, []).append(snap)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    _add_snapshot(h, make_metric("cpu", 0.5, MetricStatus.OK), age_seconds=10)
    _add_snapshot(h, make_metric("cpu", 0.8, MetricStatus.WARNING), age_seconds=5)
    _add_snapshot(h, make_metric("cpu", 0.9, MetricStatus.CRITICAL), age_seconds=1)
    _add_snapshot(h, make_metric("mem", 0.3, MetricStatus.OK), age_seconds=20)
    _add_snapshot(h, make_metric("mem", 0.4, MetricStatus.OK), age_seconds=2)
    return h


def test_rollup_metric_returns_entry(populated_history):
    entry = rollup_metric(populated_history, "cpu", window_seconds=60)
    assert isinstance(entry, RollupEntry)


def test_rollup_metric_sample_count(populated_history):
    entry = rollup_metric(populated_history, "cpu", window_seconds=60)
    assert entry.sample_count == 3


def test_rollup_metric_avg_value(populated_history):
    entry = rollup_metric(populated_history, "cpu", window_seconds=60)
    assert abs(entry.avg_value - (0.5 + 0.8 + 0.9) / 3) < 1e-9


def test_rollup_metric_min_max(populated_history):
    entry = rollup_metric(populated_history, "cpu", window_seconds=60)
    assert entry.min_value == pytest.approx(0.5)
    assert entry.max_value == pytest.approx(0.9)


def test_rollup_metric_dominant_status_is_critical(populated_history):
    entry = rollup_metric(populated_history, "cpu", window_seconds=60)
    assert entry.dominant_status == MetricStatus.CRITICAL


def test_rollup_metric_dominant_status_ok(populated_history):
    entry = rollup_metric(populated_history, "mem", window_seconds=60)
    assert entry.dominant_status == MetricStatus.OK


def test_rollup_metric_unknown_returns_none():
    h = MetricHistory()
    assert rollup_metric(h, "ghost", window_seconds=60) is None


def test_rollup_metric_excludes_old_snapshots():
    h = MetricHistory()
    _add_snapshot(h, make_metric("cpu", 1.0, MetricStatus.CRITICAL), age_seconds=200)
    _add_snapshot(h, make_metric("cpu", 0.1, MetricStatus.OK), age_seconds=5)
    entry = rollup_metric(h, "cpu", window_seconds=60)
    assert entry is not None
    assert entry.sample_count == 1
    assert entry.dominant_status == MetricStatus.OK


def test_rollup_all_returns_all_metrics(populated_history):
    entries = rollup_all(populated_history, window_seconds=60)
    names = {e.metric_name for e in entries}
    assert names == {"cpu", "mem"}


def test_dominant_status_prefers_critical():
    statuses = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL]
    assert _dominant_status(statuses) == MetricStatus.CRITICAL


def test_dominant_status_prefers_warning_over_ok():
    statuses = [MetricStatus.OK, MetricStatus.WARNING]
    assert _dominant_status(statuses) == MetricStatus.WARNING


def test_rollup_entry_str():
    h = MetricHistory()
    _add_snapshot(h, make_metric("latency", 0.42, MetricStatus.OK))
    entry = rollup_metric(h, "latency", window_seconds=60)
    assert "latency" in str(entry)
    assert "ok" in str(entry).lower()
