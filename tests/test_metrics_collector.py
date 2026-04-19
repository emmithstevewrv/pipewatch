"""Tests for metric models and the collector."""
import pytest

from pipewatch.collector import MetricCollector
from pipewatch.metrics import Metric, MetricStatus, ThresholdRule


@pytest.fixture
def rule():
    return ThresholdRule(
        metric_name="row_count",
        warning_below=100.0,
        critical_below=10.0,
        warning_above=10_000.0,
        critical_above=50_000.0,
    )


def make_metric(value: float) -> Metric:
    return Metric(name="row_count", value=value, unit="rows")


def test_ok_status(rule):
    m = make_metric(500)
    assert rule.evaluate(m) == MetricStatus.OK


def test_warning_below(rule):
    m = make_metric(50)
    assert rule.evaluate(m) == MetricStatus.WARNING


def test_critical_below(rule):
    m = make_metric(5)
    assert rule.evaluate(m) == MetricStatus.CRITICAL


def test_critical_above(rule):
    m = make_metric(60_000)
    assert rule.evaluate(m) == MetricStatus.CRITICAL


def test_collector_records_and_evaluates(rule):
    collector = MetricCollector(rules=[rule])
    m = collector.record(make_metric(5))
    assert m.status == MetricStatus.CRITICAL
    assert collector.latest("row_count") is m


def test_collector_unknown_without_rule():
    collector = MetricCollector()
    m = collector.record(make_metric(500))
    assert m.status == MetricStatus.UNKNOWN


def test_critical_metrics_returns_only_latest(rule):
    collector = MetricCollector(rules=[rule])
    collector.record(make_metric(5))    # critical
    collector.record(make_metric(500))  # ok — should supersede
    assert collector.critical_metrics() == []
