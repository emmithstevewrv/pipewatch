"""Tests for pipewatch.eviction."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.eviction import EvictionPolicy, EvictionResult, apply_eviction


def make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, unit="ms")


def _add(
    history: MetricHistory,
    name: str,
    value: float,
    status: MetricStatus = MetricStatus.OK,
    offset_seconds: int = 0,
) -> None:
    m = make_metric(name, value, status)
    ts = datetime(2024, 1, 1, 0, 0, 0) + timedelta(seconds=offset_seconds)
    history.record(m, timestamp=ts)


@pytest.fixture()
def history() -> MetricHistory:
    h = MetricHistory()
    for i in range(6):
        _add(h, "cpu", float(i), MetricStatus.OK, offset_seconds=i)
    for i in range(4):
        _add(h, "mem", float(i), MetricStatus.CRITICAL, offset_seconds=i)
    return h


def test_no_eviction_when_within_limit(history: MetricHistory) -> None:
    policy = EvictionPolicy(max_total_snapshots=100)
    results = apply_eviction(history, policy)
    assert all(r.evicted_count == 0 for r in results)


def test_total_snapshots_reduced(history: MetricHistory) -> None:
    policy = EvictionPolicy(max_total_snapshots=5, prefer_evict_ok=False)
    apply_eviction(history, policy)
    total = sum(len(history.snapshots(n)) for n in history.metric_names())
    assert total <= 5


def test_result_list_covers_all_metrics(history: MetricHistory) -> None:
    policy = EvictionPolicy(max_total_snapshots=5)
    results = apply_eviction(history, policy)
    names = {r.metric_name for r in results}
    assert names == set(history.metric_names())


def test_prefer_evict_ok_keeps_critical(history: MetricHistory) -> None:
    """When prefer_evict_ok=True, CRITICAL snapshots should be preserved over OK ones."""
    policy = EvictionPolicy(max_total_snapshots=4, prefer_evict_ok=True)
    apply_eviction(history, policy)
    # All critical (mem) snapshots should survive
    mem_snapshots = history.snapshots("mem")
    assert all(s.status == MetricStatus.CRITICAL for s in mem_snapshots)


def test_eviction_result_counts_are_consistent(history: MetricHistory) -> None:
    policy = EvictionPolicy(max_total_snapshots=6, prefer_evict_ok=False)
    results = apply_eviction(history, policy)
    for r in results:
        actual_remaining = len(history.snapshots(r.metric_name))
        assert r.remaining_count == actual_remaining


def test_eviction_policy_str() -> None:
    p = EvictionPolicy(max_total_snapshots=200, prefer_evict_ok=True)
    assert "200" in str(p)
    assert "ok-first" in str(p)


def test_eviction_result_str() -> None:
    r = EvictionResult(metric_name="latency", evicted_count=3, remaining_count=7)
    s = str(r)
    assert "latency" in s
    assert "3" in s
    assert "7" in s


def test_none_policy_uses_defaults() -> None:
    h = MetricHistory()
    for i in range(5):
        _add(h, "x", float(i), offset_seconds=i)
    results = apply_eviction(h, None)
    # Default max is 1000, so nothing should be evicted
    assert all(r.evicted_count == 0 for r in results)
