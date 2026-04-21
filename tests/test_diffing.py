"""Tests for pipewatch.diffing."""
from __futurerom datetime import datetime, timedelta

import pytest

from pipewatch.diffing import DiffEntry, diff_history, status_regressions
from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


def _add(history: MetricHistory, name: str, value: float,
         status: MetricStatus, offset_seconds: int = 0) -> None:
    m = make_metric(name, value, status)
    snap = MetricSnapshot(metric=m,
                          timestamp=datetime(2024, 1, 1) + timedelta(seconds=offset_seconds))
    history._data.setdefault(name, []).append(snap)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    _add(h, "cpu", 10.0, MetricStatus.OK, 0)
    _add(h, "cpu", 90.0, MetricStatus.CRITICAL, 10)
    _add(h, "mem", 50.0, MetricStatus.WARNING, 0)
    _add(h, "mem", 55.0, MetricStatus.WARNING, 10)
    return h


def test_diff_returns_entry_per_metric(populated_history):
    diffs = diff_history(populated_history)
    assert len(diffs) == 2
    names = {d.metric_name for d in diffs}
    assert names == {"cpu", "mem"}


def test_diff_value_delta(populated_history):
    diffs = diff_history(populated_history)
    cpu_diff = next(d for d in diffs if d.metric_name == "cpu")
    assert cpu_diff.value_delta == pytest.approx(80.0)


def test_diff_status_changed(populated_history):
    diffs = diff_history(populated_history)
    cpu_diff = next(d for d in diffs if d.metric_name == "cpu")
    assert cpu_diff.status_changed is True


def test_diff_status_unchanged(populated_history):
    diffs = diff_history(populated_history)
    mem_diff = next(d for d in diffs if d.metric_name == "mem")
    assert mem_diff.status_changed is False


def test_status_regressions_filters_correctly(populated_history):
    diffs = diff_history(populated_history)
    regressions = status_regressions(diffs)
    assert len(regressions) == 1
    assert regressions[0].metric_name == "cpu"


def test_diff_entry_str():
    entry = DiffEntry(
        metric_name="latency",
        old_value=10.0,
        new_value=20.0,
        old_status=MetricStatus.OK,
        new_status=MetricStatus.WARNING,
    )
    s = str(entry)
    assert "latency" in s
    assert "+10" in s


def test_diff_with_single_snapshot():
    h = MetricHistory()
    _add(h, "disk", 40.0, MetricStatus.OK, 0)
    diffs = diff_history(h, window=2)
    assert len(diffs) == 1
    assert diffs[0].value_delta == pytest.approx(0.0)
