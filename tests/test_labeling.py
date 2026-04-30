"""Tests for pipewatch.labeling."""

from __future__ import annotations

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.labeling import (
    LabeledSnapshot,
    label_snapshots,
    filter_by_label,
    group_by_label,
)


def make_metric(name: str, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def populated_history() -> MetricHistory:
    h = MetricHistory()
    for name in ("cpu", "memory", "latency"):
        for v in (10.0, 20.0, 30.0):
            h.record(MetricSnapshot(metric=make_metric(name, v)))
    return h


def test_label_snapshots_returns_all():
    h = populated_history()
    labeled = label_snapshots(h, {})
    assert len(labeled) == 9  # 3 metrics * 3 snapshots


def test_label_snapshots_attaches_correct_labels():
    h = populated_history()
    label_map = {"cpu": {"team": "infra"}, "memory": {"team": "platform"}}
    labeled = label_snapshots(h, label_map)
    cpu_items = [ls for ls in labeled if ls.snapshot.metric.name == "cpu"]
    assert all(ls.labels.get("team") == "infra" for ls in cpu_items)


def test_unlabeled_metric_gets_empty_labels():
    h = populated_history()
    labeled = label_snapshots(h, {})
    latency_items = [ls for ls in labeled if ls.snapshot.metric.name == "latency"]
    assert all(ls.labels == {} for ls in latency_items)


def test_has_label_key_only():
    snap = MetricSnapshot(metric=make_metric("cpu"))
    ls = LabeledSnapshot(snapshot=snap, labels={"env": "prod"})
    assert ls.has_label("env") is True
    assert ls.has_label("region") is False


def test_has_label_key_and_value():
    snap = MetricSnapshot(metric=make_metric("cpu"))
    ls = LabeledSnapshot(snapshot=snap, labels={"env": "prod"})
    assert ls.has_label("env", "prod") is True
    assert ls.has_label("env", "staging") is False


def test_filter_by_label_returns_matching():
    h = populated_history()
    label_map = {"cpu": {"tier": "high"}, "memory": {"tier": "low"}}
    labeled = label_snapshots(h, label_map)
    high = filter_by_label(labeled, "tier", "high")
    assert all(ls.snapshot.metric.name == "cpu" for ls in high)
    assert len(high) == 3


def test_filter_by_label_key_only():
    h = populated_history()
    label_map = {"cpu": {"tier": "high"}, "memory": {"tier": "low"}}
    labeled = label_snapshots(h, label_map)
    tiered = filter_by_label(labeled, "tier")
    assert len(tiered) == 6  # cpu + memory


def test_group_by_label_creates_correct_buckets():
    h = populated_history()
    label_map = {"cpu": {"env": "prod"}, "memory": {"env": "staging"}}
    labeled = label_snapshots(h, label_map)
    groups = group_by_label(labeled, "env")
    assert "prod" in groups
    assert "staging" in groups
    assert len(groups["prod"]) == 3
    assert len(groups["staging"]) == 3


def test_group_by_label_missing_key_goes_to_empty_bucket():
    h = populated_history()
    labeled = label_snapshots(h, {})  # no labels at all
    groups = group_by_label(labeled, "env")
    assert "" in groups
    assert len(groups[""]) == 9


def test_labeled_snapshot_str():
    snap = MetricSnapshot(metric=make_metric("cpu"))
    ls = LabeledSnapshot(snapshot=snap, labels={"env": "prod", "tier": "high"})
    s = str(ls)
    assert "cpu" in s
    assert "env=prod" in s
    assert "tier=high" in s
