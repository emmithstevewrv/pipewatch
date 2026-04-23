"""Tests for pipewatch.partitioning."""

from __future__ import annotations

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.partitioning import Partition, partition_all, partition_metric


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="")


BOUNDS = [("low", 0.0, 33.0), ("mid", 33.0, 66.0), ("high", 66.0, 100.0)]


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    for v in [10.0, 20.0, 40.0, 50.0, 70.0, 90.0]:
        h.record(make_metric("cpu", v))
    for v in [5.0, 80.0]:
        h.record(make_metric("mem", v))
    return h


def test_returns_none_for_unknown_metric(populated_history: MetricHistory) -> None:
    result = partition_metric(populated_history, "nonexistent", BOUNDS)
    assert result is None


def test_partition_count_matches_bounds(populated_history: MetricHistory) -> None:
    result = partition_metric(populated_history, "cpu", BOUNDS)
    assert result is not None
    assert len(result) == len(BOUNDS)


def test_snapshots_distributed_correctly(populated_history: MetricHistory) -> None:
    result = partition_metric(populated_history, "cpu", BOUNDS)
    assert result is not None
    counts = {p.label: p.count for p in result}
    assert counts["low"] == 2   # 10, 20
    assert counts["mid"] == 2   # 40, 50
    assert counts["high"] == 2  # 70, 90


def test_mean_is_none_for_empty_partition() -> None:
    h = MetricHistory()
    h.record(make_metric("x", 5.0))
    result = partition_metric(h, "x", BOUNDS)
    assert result is not None
    mid = next(p for p in result if p.label == "mid")
    assert mid.mean is None


def test_mean_computed_correctly(populated_history: MetricHistory) -> None:
    result = partition_metric(populated_history, "cpu", BOUNDS)
    assert result is not None
    low_part = next(p for p in result if p.label == "low")
    assert low_part.mean == pytest.approx(15.0)


def test_partition_all_covers_all_metrics(populated_history: MetricHistory) -> None:
    result = partition_all(populated_history, BOUNDS)
    assert set(result.keys()) == {"cpu", "mem"}


def test_partition_str_representation() -> None:
    p = Partition(label="low", low=0.0, high=33.0)
    assert "low" in str(p)
    assert "0.0" in str(p)
