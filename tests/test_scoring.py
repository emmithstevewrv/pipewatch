"""Tests for pipewatch.scoring."""

from __future__ import annotations

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.scoring import score_metric, score_all, ScoredMetric


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def history() -> MetricHistory:
    return MetricHistory()


def _add(history: MetricHistory, name: str, status: MetricStatus, n: int = 1) -> None:
    for _ in range(n):
        history.record(make_metric(name, 1.0, status))


# ── score_metric ─────────────────────────────────────────────────────────────

def test_returns_none_for_unknown_metric(history):
    assert score_metric(history, "missing") is None


def test_all_ok_gives_perfect_score(history):
    _add(history, "cpu", MetricStatus.OK, n=10)
    result = score_metric(history, "cpu")
    assert result is not None
    assert result.score == pytest.approx(100.0)
    assert result.ok_ratio == pytest.approx(1.0)
    assert result.critical_ratio == pytest.approx(0.0)


def test_all_critical_gives_zero_score(history):
    _add(history, "cpu", MetricStatus.CRITICAL, n=5)
    result = score_metric(history, "cpu")
    assert result is not None
    assert result.score == pytest.approx(0.0)
    assert result.critical_ratio == pytest.approx(1.0)


def test_all_warning_gives_fifty_score(history):
    _add(history, "cpu", MetricStatus.WARNING, n=4)
    result = score_metric(history, "cpu")
    assert result is not None
    assert result.score == pytest.approx(50.0)
    assert result.warning_ratio == pytest.approx(1.0)


def test_mixed_statuses_score(history):
    # 5 OK + 5 CRITICAL → avg weight = 0.5 → score = 50
    _add(history, "db", MetricStatus.OK, n=5)
    _add(history, "db", MetricStatus.CRITICAL, n=5)
    result = score_metric(history, "db")
    assert result is not None
    assert result.score == pytest.approx(50.0)
    assert result.sample_count == 10


def test_sample_count_is_correct(history):
    _add(history, "latency", MetricStatus.OK, n=7)
    result = score_metric(history, "latency")
    assert result.sample_count == 7


# ── score_all ─────────────────────────────────────────────────────────────────

def test_score_all_returns_all_metrics(history):
    _add(history, "a", MetricStatus.OK, n=3)
    _add(history, "b", MetricStatus.CRITICAL, n=3)
    results = score_all(history)
    names = {r.metric_name for r in results}
    assert names == {"a", "b"}


def test_score_all_sorted_ascending(history):
    _add(history, "good", MetricStatus.OK, n=5)
    _add(history, "bad", MetricStatus.CRITICAL, n=5)
    results = score_all(history)
    scores = [r.score for r in results]
    assert scores == sorted(scores)


def test_score_all_empty_history():
    assert score_all(MetricHistory()) == []


def test_str_representation(history):
    _add(history, "x", MetricStatus.OK, n=2)
    result = score_metric(history, "x")
    assert "x" in str(result)
    assert "score=" in str(result)
