"""Tests for pipewatch.ranking."""

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.ranking import rank_by_severity, rank_by_value, top_n


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    h.record(make_metric("rows_processed", 500.0, MetricStatus.OK))
    h.record(make_metric("error_rate", 0.15, MetricStatus.CRITICAL))
    h.record(make_metric("latency_ms", 320.0, MetricStatus.WARNING))
    h.record(make_metric("queue_depth", 12.0, MetricStatus.OK))
    return h


def test_rank_by_value_descending(populated_history: MetricHistory) -> None:
    ranked = rank_by_value(populated_history, descending=True)
    values = [r.latest_value for r in ranked]
    assert values == sorted(values, reverse=True)


def test_rank_by_value_ascending(populated_history: MetricHistory) -> None:
    ranked = rank_by_value(populated_history, descending=False)
    values = [r.latest_value for r in ranked]
    assert values == sorted(values)


def test_rank_numbers_are_sequential(populated_history: MetricHistory) -> None:
    ranked = rank_by_value(populated_history)
    ranks = [r.rank for r in ranked]
    assert ranks == list(range(1, len(ranks) + 1))


def test_rank_by_severity_critical_first(populated_history: MetricHistory) -> None:
    ranked = rank_by_severity(populated_history)
    assert ranked[0].status == MetricStatus.CRITICAL


def test_rank_by_severity_warning_before_ok(populated_history: MetricHistory) -> None:
    ranked = rank_by_severity(populated_history)
    statuses = [r.status for r in ranked]
    warning_idx = next(i for i, s in enumerate(statuses) if s == MetricStatus.WARNING)
    ok_indices = [i for i, s in enumerate(statuses) if s == MetricStatus.OK]
    assert all(warning_idx < oi for oi in ok_indices)


def test_top_n_limits_results(populated_history: MetricHistory) -> None:
    ranked = rank_by_value(populated_history)
    top = top_n(ranked, 2)
    assert len(top) == 2
    assert top[0].rank == 1
    assert top[1].rank == 2


def test_top_n_larger_than_list(populated_history: MetricHistory) -> None:
    ranked = rank_by_value(populated_history)
    top = top_n(ranked, 100)
    assert len(top) == len(ranked)


def test_empty_history_returns_empty_list() -> None:
    h = MetricHistory()
    assert rank_by_value(h) == []
    assert rank_by_severity(h) == []


def test_ranked_metric_str() -> None:
    from pipewatch.ranking import RankedMetric
    r = RankedMetric(name="cpu", latest_value=0.85, status=MetricStatus.WARNING, sample_count=10, rank=1)
    s = str(r)
    assert "#1" in s
    assert "cpu" in s
    assert "warning" in s.lower()
