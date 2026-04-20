"""Tests for pipewatch.tagging."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.tagging import (
    TaggedSnapshot,
    filter_by_tag,
    group_by_tag,
    tag_snapshots,
)


def make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    for name in ("cpu", "memory"):
        for i in range(3):
            h.record(make_metric(name, float(i * 10)))
    return h


def test_tag_snapshots_returns_all(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {"env": "prod"})
    assert len(tagged) == 6  # 2 metrics × 3 snapshots each


def test_tag_snapshots_single_metric(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {"env": "prod"}, metric_name="cpu")
    assert len(tagged) == 3
    assert all(t.snapshot.name == "cpu" for t in tagged)


def test_tags_are_attached(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {"env": "staging", "team": "data"})
    for t in tagged:
        assert t.tags["env"] == "staging"
        assert t.tags["team"] == "data"


def test_has_tag_key_only(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {"env": "prod"})
    assert tagged[0].has_tag("env")
    assert not tagged[0].has_tag("region")


def test_has_tag_key_and_value(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {"env": "prod"})
    assert tagged[0].has_tag("env", "prod")
    assert not tagged[0].has_tag("env", "staging")


def test_filter_by_tag_returns_matching(populated_history: MetricHistory) -> None:
    cpu_tagged = tag_snapshots(populated_history, {"metric": "cpu"}, metric_name="cpu")
    mem_tagged = tag_snapshots(populated_history, {"metric": "memory"}, metric_name="memory")
    all_tagged = cpu_tagged + mem_tagged

    filtered = filter_by_tag(all_tagged, "metric", "cpu")
    assert len(filtered) == 3
    assert all(t.snapshot.name == "cpu" for t in filtered)


def test_filter_by_tag_no_match(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {"env": "prod"})
    filtered = filter_by_tag(tagged, "env", "dev")
    assert filtered == []


def test_group_by_tag(populated_history: MetricHistory) -> None:
    cpu_tagged = tag_snapshots(populated_history, {"team": "infra"}, metric_name="cpu")
    mem_tagged = tag_snapshots(populated_history, {"team": "data"}, metric_name="memory")
    groups = group_by_tag(cpu_tagged + mem_tagged, "team")

    assert set(groups.keys()) == {"infra", "data"}
    assert len(groups["infra"]) == 3
    assert len(groups["data"]) == 3


def test_group_by_tag_missing_key(populated_history: MetricHistory) -> None:
    tagged = tag_snapshots(populated_history, {})
    groups = group_by_tag(tagged, "env")
    assert "" in groups
    assert len(groups[""]) == 6
