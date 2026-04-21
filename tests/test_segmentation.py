"""Tests for pipewatch.segmentation."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.segmentation import Segment, segment_metric, segment_all


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, message="ok")


@pytest.fixture
def populated_history() -> MetricHistory:
    history = MetricHistory()
    base = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(20):
        ts = base + timedelta(seconds=i * 10)
        history.record(make_metric("latency", float(i)), timestamp=ts)
    return history


def test_segment_count_matches_num_windows(populated_history):
    ref = datetime(2024, 1, 1, 12, 3, 20)
    segs = segment_metric(populated_history, "latency", timedelta(seconds=60), 3, ref)
    assert len(segs) == 3


def test_segment_labels_ordered(populated_history):
    ref = datetime(2024, 1, 1, 12, 3, 20)
    segs = segment_metric(populated_history, "latency", timedelta(seconds=60), 3, ref)
    assert segs[-1].label == "current"
    assert segs[0].label == "T-2"


def test_snapshots_fall_within_window(populated_history):
    ref = datetime(2024, 1, 1, 12, 3, 20)
    segs = segment_metric(populated_history, "latency", timedelta(seconds=60), 3, ref)
    for seg in segs:
        for snap in seg.snapshots:
            assert seg.start <= snap.timestamp < seg.end


def test_mean_is_none_for_empty_segment():
    seg = Segment(label="T-0", start=datetime.utcnow(), end=datetime.utcnow(), snapshots=[])
    assert seg.mean is None


def test_mean_computed_correctly(populated_history):
    ref = datetime(2024, 1, 1, 12, 0, 30)
    segs = segment_metric(populated_history, "latency", timedelta(seconds=30), 1, ref)
    seg = segs[0]
    if seg.sample_count > 0:
        expected = sum(seg.values) / seg.sample_count
        assert abs(seg.mean - expected) < 1e-9


def test_segment_all_returns_all_metrics():
    history = MetricHistory()
    base = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(5):
        ts = base + timedelta(seconds=i * 10)
        history.record(make_metric("cpu", float(i)), timestamp=ts)
        history.record(make_metric("mem", float(i * 2)), timestamp=ts)

    ref = datetime(2024, 1, 1, 12, 1, 0)
    result = segment_all(history, timedelta(seconds=30), 2, ref)
    assert set(result.keys()) == {"cpu", "mem"}


def test_segment_str_representation():
    seg = Segment(
        label="current",
        start=datetime(2024, 1, 1, 12, 0, 0),
        end=datetime(2024, 1, 1, 12, 1, 0),
        snapshots=[],
    )
    s = str(seg)
    assert "current" in s
    assert "n=0" in s
    assert "n/a" in s


def test_unknown_metric_returns_empty_segments():
    history = MetricHistory()
    ref = datetime(2024, 1, 1, 12, 0, 0)
    segs = segment_metric(history, "ghost", timedelta(seconds=60), 3, ref)
    assert len(segs) == 3
    assert all(s.sample_count == 0 for s in segs)
