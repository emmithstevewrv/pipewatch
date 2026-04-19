"""Tests for pipewatch.report module."""
import pytest
from datetime import datetime

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.report import build_report, MetricSummary


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status, timestamp=datetime.utcnow())


@pytest.fixture
def populated_history() -> MetricHistory:
    h = MetricHistory()
    for v in [1.0, 2.0, 3.0]:
        h.record(make_metric("rows_processed", v, MetricStatus.OK))
    for v in [90.0, 95.0]:
        h.record(make_metric("error_rate", v, MetricStatus.CRITICAL))
    return h


def test_report_contains_all_metrics(populated_history):
    report = build_report(populated_history)
    names = {s.name for s in report.summaries}
    assert "rows_processed" in names
    assert "error_rate" in names


def test_sample_count(populated_history):
    report = build_report(populated_history)
    rp = next(s for s in report.summaries if s.name == "rows_processed")
    assert rp.sample_count == 3


def test_min_max_avg(populated_history):
    report = build_report(populated_history)
    rp = next(s for s in report.summaries if s.name == "rows_processed")
    assert rp.min_value == pytest.approx(1.0)
    assert rp.max_value == pytest.approx(3.0)
    assert rp.avg_value == pytest.approx(2.0)


def test_latest_value(populated_history):
    report = build_report(populated_history)
    rp = next(s for s in report.summaries if s.name == "rows_processed")
    assert rp.latest_value == pytest.approx(3.0)


def test_latest_status(populated_history):
    report = build_report(populated_history)
    er = next(s for s in report.summaries if s.name == "error_rate")
    assert er.latest_status == MetricStatus.CRITICAL


def test_counts(populated_history):
    report = build_report(populated_history)
    assert report.ok_count == 1
    assert report.critical_count == 1
    assert report.warning_count == 0


def test_empty_history():
    report = build_report(MetricHistory())
    assert report.summaries == []
    assert report.ok_count == 0
