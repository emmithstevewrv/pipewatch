"""Tests for pipewatch.compression."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.compression import compress_metric, compress_all, _lttb
from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _add(history: MetricHistory, name: str, values: List[float]) -> None:
    now = datetime.now(tz=timezone.utc).timestamp()
    for i, v in enumerate(values):
        snap = MetricSnapshot(
            metric=make_metric(name, v),
            timestamp=now + i,
        )
        history.record(snap)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    _add(h, "cpu", [float(i) for i in range(100)])
    _add(h, "mem", [float(50 + i % 10) for i in range(80)])
    return h


# --- _lttb unit tests ---

def test_lttb_returns_all_when_below_threshold():
    h = MetricHistory()
    _add(h, "x", [1.0, 2.0, 3.0])
    snaps = h.snapshots("x")
    result = _lttb(snaps, threshold=10)
    assert len(result) == 3


def test_lttb_respects_threshold():
    h = MetricHistory()
    _add(h, "x", [float(i) for i in range(200)])
    snaps = h.snapshots("x")
    result = _lttb(snaps, threshold=40)
    assert len(result) == 40


def test_lttb_preserves_first_and_last():
    h = MetricHistory()
    values = [float(i) for i in range(100)]
    _add(h, "x", values)
    snaps = h.snapshots("x")
    result = _lttb(snaps, threshold=20)
    assert result[0] is snaps[0]
    assert result[-1] is snaps[-1]


# --- compress_metric ---

def test_compress_metric_returns_none_for_unknown(populated_history):
    assert compress_metric(populated_history, "nonexistent") is None


def test_compress_metric_original_count(populated_history):
    result = compress_metric(populated_history, "cpu", threshold=30)
    assert result is not None
    assert result.original_count == 100


def test_compress_metric_compressed_count(populated_history):
    result = compress_metric(populated_history, "cpu", threshold=30)
    assert result is not None
    assert result.compressed_count == 30


def test_compress_metric_str_contains_name(populated_history):
    result = compress_metric(populated_history, "cpu", threshold=30)
    assert result is not None
    assert "cpu" in str(result)


# --- compress_all ---

def test_compress_all_returns_entry_per_metric(populated_history):
    results = compress_all(populated_history, threshold=20)
    names = {r.metric_name for r in results}
    assert "cpu" in names
    assert "mem" in names


def test_compress_all_empty_history():
    results = compress_all(MetricHistory(), threshold=20)
    assert results == []
