"""Tests for pipewatch.watermark."""
from __future__ import annotations

import datetime
from typing import List

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.watermark import (
    WatermarkEntry,
    compute_watermarks,
    compute_all_watermarks,
)


def make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    base = datetime.datetime(2024, 1, 1, 12, 0, 0)
    for i, (val, status) in enumerate(
        [
            (10.0, MetricStatus.OK),
            (50.0, MetricStatus.WARNING),
            (5.0, MetricStatus.CRITICAL),
            (30.0, MetricStatus.OK),
        ]
    ):
        h.record(make_metric("cpu", val, status), timestamp=base + datetime.timedelta(seconds=i))
    h.record(make_metric("mem", 80.0, MetricStatus.CRITICAL), timestamp=base)
    h.record(make_metric("mem", 20.0, MetricStatus.OK), timestamp=base + datetime.timedelta(seconds=1))
    return h


def test_returns_none_for_unknown_metric(populated_history: MetricHistory) -> None:
    result = compute_watermarks(populated_history, "nonexistent")
    assert result is None


def test_high_watermark_value(populated_history: MetricHistory) -> None:
    result = compute_watermarks(populated_history, "cpu")
    assert result is not None
    assert result.high == 50.0


def test_low_watermark_value(populated_history: MetricHistory) -> None:
    result = compute_watermarks(populated_history, "cpu")
    assert result is not None
    assert result.low == 5.0


def test_high_watermark_status(populated_history: MetricHistory) -> None:
    result = compute_watermarks(populated_history, "cpu")
    assert result is not None
    assert result.high_status == MetricStatus.WARNING


def test_low_watermark_status(populated_history: MetricHistory) -> None:
    result = compute_watermarks(populated_history, "cpu")
    assert result is not None
    assert result.low_status == MetricStatus.CRITICAL


def test_sample_count(populated_history: MetricHistory) -> None:
    result = compute_watermarks(populated_history, "cpu")
    assert result is not None
    assert result.sample_count == 4


def test_compute_all_returns_all_metrics(populated_history: MetricHistory) -> None:
    results = compute_all_watermarks(populated_history)
    names = [r.metric_name for r in results]
    assert "cpu" in names
    assert "mem" in names


def test_compute_all_sorted_by_name(populated_history: MetricHistory) -> None:
    results = compute_all_watermarks(populated_history)
    names = [r.metric_name for r in results]
    assert names == sorted(names)


def test_str_representation() -> None:
    entry = WatermarkEntry(
        metric_name="latency",
        high=99.9,
        low=1.1,
        high_status=MetricStatus.CRITICAL,
        low_status=MetricStatus.OK,
        sample_count=10,
    )
    s = str(entry)
    assert "latency" in s
    assert "high" in s
    assert "low" in s
