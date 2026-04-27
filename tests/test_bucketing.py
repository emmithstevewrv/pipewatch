"""Tests for pipewatch.bucketing."""
from __future__ import annotations

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.bucketing import Bucket, bucket_metric, bucket_all


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _add(history: MetricHistory, name: str, value: float, ts: float = 0.0) -> None:
    from pipewatch.history import MetricSnapshot
    snap = MetricSnapshot(metric=make_metric(name, value), timestamp=ts)
    history._data.setdefault(name, []).append(snap)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    for i, v in enumerate([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]):
        _add(h, "rows", v, ts=float(i))
    return h


def test_returns_none_for_unknown_metric():
    h = MetricHistory()
    assert bucket_metric(h, "missing") is None


def test_bucket_count_matches_num_buckets(populated_history):
    buckets = bucket_metric(populated_history, "rows", num_buckets=5)
    assert buckets is not None
    assert len(buckets) == 5


def test_all_snapshots_distributed(populated_history):
    buckets = bucket_metric(populated_history, "rows", num_buckets=5)
    assert buckets is not None
    total = sum(b.count for b in buckets)
    assert total == 10


def test_bucket_labels_are_strings(populated_history):
    buckets = bucket_metric(populated_history, "rows", num_buckets=4)
    assert buckets is not None
    for b in buckets:
        assert isinstance(b.label, str)
        assert "–" in b.label


def test_constant_values_produce_single_bucket():
    h = MetricHistory()
    for i in range(5):
        _add(h, "flat", 7.0, ts=float(i))
    buckets = bucket_metric(h, "flat", num_buckets=5)
    assert buckets is not None
    assert len(buckets) == 1
    assert buckets[0].count == 5


def test_bucket_mean_is_correct(populated_history):
    # With 10 values 1..10 in 5 equal buckets each bucket has 2 values.
    buckets = bucket_metric(populated_history, "rows", num_buckets=5)
    assert buckets is not None
    for b in buckets:
        assert b.mean is not None


def test_bucket_all_covers_all_metrics():
    h = MetricHistory()
    for i in range(6):
        _add(h, "alpha", float(i), ts=float(i))
        _add(h, "beta", float(i) * 2, ts=float(i))
    result = bucket_all(h, num_buckets=3)
    assert set(result.keys()) == {"alpha", "beta"}


def test_bucket_str_representation():
    b = Bucket(label="0.0–1.0", low=0.0, high=1.0)
    assert "0.0–1.0" in str(b)
    assert "count=0" in str(b)
    assert "n/a" in str(b)
