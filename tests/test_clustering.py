"""Tests for pipewatch.clustering."""
from __future__ import annotations

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.clustering import cluster_metrics, Cluster


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="")


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    # Three clearly separated groups
    for v in [1.0, 1.1, 0.9]:
        h.record(make_metric("low", v))
    for v in [50.0, 51.0, 49.0]:
        h.record(make_metric("mid", v))
    for v in [99.0, 100.0, 101.0]:
        h.record(make_metric("high", v))
    return h


def test_returns_empty_for_single_metric():
    h = MetricHistory()
    h.record(make_metric("only", 5.0))
    result = cluster_metrics(h, n_clusters=3)
    assert result == []


def test_returns_empty_for_no_metrics():
    h = MetricHistory()
    result = cluster_metrics(h, n_clusters=3)
    assert result == []


def test_cluster_count_does_not_exceed_n(populated_history):
    result = cluster_metrics(populated_history, n_clusters=3)
    assert len(result) <= 3


def test_all_metrics_are_assigned(populated_history):
    result = cluster_metrics(populated_history, n_clusters=3)
    assigned = [name for c in result for name in c.metric_names]
    assert sorted(assigned) == ["high", "low", "mid"]


def test_centroid_within_min_max(populated_history):
    result = cluster_metrics(populated_history, n_clusters=3)
    for cluster in result:
        assert cluster.min_value <= cluster.centroid <= cluster.max_value


def test_metric_name_filter():
    h = MetricHistory()
    for v in [1.0, 2.0]:
        h.record(make_metric("a", v))
    for v in [100.0, 101.0]:
        h.record(make_metric("b", v))
    for v in [200.0, 201.0]:
        h.record(make_metric("c", v))

    result = cluster_metrics(h, n_clusters=2, metric_names=["a", "b"])
    assigned = [name for cl in result for name in cl.metric_names]
    assert "c" not in assigned
    assert sorted(assigned) == ["a", "b"]


def test_cluster_str_contains_label(populated_history):
    result = cluster_metrics(populated_history, n_clusters=3)
    for cluster in result:
        assert cluster.label in str(cluster)
        assert "centroid" in str(cluster)
