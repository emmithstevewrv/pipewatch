"""Tests for pipewatch.pipeline."""
from __future__ import annotations

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.pipeline import PipelineHealth, _score, pipeline_health


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def history_with_pipelines() -> tuple[MetricHistory, dict[str, str]]:
    h = MetricHistory()
    tags: dict[str, str] = {}

    for name, status, pipeline in [
        ("etl.rows", MetricStatus.OK, "ingest"),
        ("etl.lag", MetricStatus.WARNING, "ingest"),
        ("etl.errors", MetricStatus.CRITICAL, "ingest"),
        ("ml.accuracy", MetricStatus.OK, "ml"),
        ("ml.latency", MetricStatus.OK, "ml"),
    ]:
        h.record(make_metric(name, 1.0, status))
        tags[name] = pipeline

    return h, tags


def test_score_all_ok():
    assert _score(5, 0, 0) == pytest.approx(1.0)


def test_score_all_critical():
    assert _score(0, 0, 5) == pytest.approx(0.0)


def test_score_mixed():
    # 2 ok, 2 warning, 0 critical  ->  (2*1 + 2*0.5) / 4 = 0.75
    assert _score(2, 2, 0) == pytest.approx(0.75)


def test_score_empty():
    assert _score(0, 0, 0) == pytest.approx(1.0)


def test_pipeline_health_returns_one_entry_per_pipeline(history_with_pipelines):
    h, tags = history_with_pipelines
    results = pipeline_health(h, tags)
    pipelines = {r.pipeline for r in results}
    assert pipelines == {"ingest", "ml"}


def test_ml_pipeline_fully_healthy(history_with_pipelines):
    h, tags = history_with_pipelines
    results = pipeline_health(h, tags)
    ml = next(r for r in results if r.pipeline == "ml")
    assert ml.ok == 2
    assert ml.warning == 0
    assert ml.critical == 0
    assert ml.score == pytest.approx(1.0)


def test_ingest_pipeline_has_all_statuses(history_with_pipelines):
    h, tags = history_with_pipelines
    results = pipeline_health(h, tags)
    ingest = next(r for r in results if r.pipeline == "ingest")
    assert ingest.ok == 1
    assert ingest.warning == 1
    assert ingest.critical == 1
    assert ingest.total == 3


def test_results_sorted_best_first(history_with_pipelines):
    h, tags = history_with_pipelines
    results = pipeline_health(h, tags)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_unknown_metric_skipped():
    h = MetricHistory()
    # tags reference a metric that was never recorded
    results = pipeline_health(h, {"missing.metric": "ghost"})
    assert results == []
