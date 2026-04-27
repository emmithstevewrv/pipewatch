"""Tests for pipewatch.summarization."""

from __future__ import annotations

import time

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.summarization import HealthDigest, MetricDigest, summarize


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    base = time.time() - 100
    statuses = [
        MetricStatus.OK,
        MetricStatus.OK,
        MetricStatus.WARNING,
        MetricStatus.CRITICAL,
        MetricStatus.OK,
    ]
    for i, st in enumerate(statuses):
        h.record(make_metric("pipe_a", float(i), st), timestamp=base + i)
    h.record(make_metric("pipe_b", 99.0, MetricStatus.CRITICAL), timestamp=base)
    return h


def test_digest_contains_all_metrics(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    names = {m.name for m in digest.metrics}
    assert "pipe_a" in names
    assert "pipe_b" in names


def test_total_metrics_count(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    assert digest.total_metrics == 2


def test_total_samples_count(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    assert digest.total_samples == 6  # 5 + 1


def test_latest_status_reflects_last_snapshot(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    pipe_a = next(m for m in digest.metrics if m.name == "pipe_a")
    assert pipe_a.latest_status == MetricStatus.OK


def test_percentages_sum_to_100(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    for m in digest.metrics:
        total = m.ok_pct + m.warning_pct + m.critical_pct
        assert abs(total - 100.0) < 1e-6


def test_dominant_status_is_most_frequent(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    pipe_a = next(m for m in digest.metrics if m.name == "pipe_a")
    # 3 OK, 1 WARNING, 1 CRITICAL  → dominant = OK
    assert pipe_a.dominant_status == MetricStatus.OK


def test_critical_metrics_property(populated_history: MetricHistory) -> None:
    digest = summarize(populated_history)
    crits = digest.critical_metrics
    assert any(m.name == "pipe_b" for m in crits)


def test_empty_history_returns_empty_digest() -> None:
    digest = summarize(MetricHistory())
    assert digest.total_metrics == 0
    assert digest.total_samples == 0
    assert digest.metrics == []


def test_single_sample_percentages() -> None:
    h = MetricHistory()
    h.record(make_metric("x", 1.0, MetricStatus.WARNING))
    digest = summarize(h)
    m = digest.metrics[0]
    assert m.warning_pct == pytest.approx(100.0)
    assert m.ok_pct == pytest.approx(0.0)
    assert m.critical_pct == pytest.approx(0.0)
