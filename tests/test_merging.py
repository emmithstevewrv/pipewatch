"""Tests for pipewatch.merging."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipewatch.history import MetricHistory
from pipewatch.merging import merge_histories
from pipewatch.metrics import Metric, MetricStatus


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="ms")


def _ts(offset: float) -> float:
    """Return a fixed base timestamp plus *offset* seconds."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    return base + offset


def _add(history: MetricHistory, name: str, value: float, offset: float) -> None:
    metric = make_metric(name, value)
    history.record(metric, timestamp=_ts(offset))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def two_histories():
    h1 = MetricHistory()
    h2 = MetricHistory()
    _add(h1, "cpu", 10.0, 0)
    _add(h1, "cpu", 20.0, 1)
    _add(h2, "cpu", 30.0, 2)
    _add(h2, "mem", 50.0, 0)
    return h1, h2


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_merge_combines_metric_names(two_histories):
    h1, h2 = two_histories
    result = merge_histories(h1, h2)
    assert "cpu" in result.metric_names
    assert "mem" in result.metric_names


def test_merge_snapshot_count(two_histories):
    h1, h2 = two_histories
    result = merge_histories(h1, h2)
    # h1 has 2 cpu snapshots, h2 adds 1 more (different timestamp)
    assert len(result.snapshots["cpu"]) == 3
    assert len(result.snapshots["mem"]) == 1


def test_merge_snapshots_are_sorted(two_histories):
    h1, h2 = two_histories
    result = merge_histories(h1, h2)
    ts_list = [s.timestamp for s in result.snapshots["cpu"]]
    assert ts_list == sorted(ts_list)


def test_merge_conflict_resolution():
    """When both histories have the same metric+timestamp, h2 wins."""
    h1 = MetricHistory()
    h2 = MetricHistory()
    _add(h1, "cpu", 10.0, 0)  # timestamp 0 in h1
    _add(h2, "cpu", 99.0, 0)  # same timestamp in h2 — should win
    result = merge_histories(h1, h2)
    assert result.conflicts == 1
    latest = result.latest("cpu")
    assert latest is not None
    assert latest.metric.value == 99.0


def test_merge_no_conflicts_when_timestamps_differ(two_histories):
    h1, h2 = two_histories
    result = merge_histories(h1, h2)
    assert result.conflicts == 0


def test_merge_single_history():
    h = MetricHistory()
    _add(h, "latency", 5.0, 0)
    _add(h, "latency", 6.0, 1)
    result = merge_histories(h)
    assert result.metric_names == ["latency"]
    assert len(result.snapshots["latency"]) == 2


def test_merge_empty_histories():
    result = merge_histories(MetricHistory(), MetricHistory())
    assert result.metric_names == []
    assert result.conflicts == 0


def test_str_representation(two_histories):
    h1, h2 = two_histories
    result = merge_histories(h1, h2)
    text = str(result)
    assert "MergeResult" in text
    assert "metrics=2" in text
