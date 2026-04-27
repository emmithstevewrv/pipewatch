"""Tests for pipewatch.replay."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.replay import ReplayConfig, ReplayResult, replay_history


def make_metric(name: str, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="ms")


def _add(history: MetricHistory, name: str, value: float, ts: float) -> None:
    metric = make_metric(name, value)
    snapshot = MetricSnapshot(metric=metric, timestamp=ts)
    history.record(snapshot)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    base = 1_000_000.0
    for i in range(5):
        _add(h, "rows_processed", float(i * 10), base + i * 60)
        _add(h, "error_rate", float(i), base + i * 60 + 1)
    return h


def _no_sleep(seconds: float) -> None:  # noqa: ARG001
    pass


# ---------------------------------------------------------------------------
# replay_history
# ---------------------------------------------------------------------------

def test_all_snapshots_replayed(populated_history: MetricHistory) -> None:
    seen: List[MetricSnapshot] = []
    result = replay_history(populated_history, seen.append, _sleep=_no_sleep)
    assert result.replayed == 10
    assert result.skipped == 0


def test_snapshots_in_chronological_order(populated_history: MetricHistory) -> None:
    seen: List[MetricSnapshot] = []
    replay_history(populated_history, seen.append, _sleep=_no_sleep)
    timestamps = [s.timestamp for s in seen]
    assert timestamps == sorted(timestamps)


def test_metrics_seen_populated(populated_history: MetricHistory) -> None:
    result = replay_history(populated_history, lambda s: None, _sleep=_no_sleep)
    assert set(result.metrics_seen) == {"rows_processed", "error_rate"}


def test_max_snapshots_caps_replay(populated_history: MetricHistory) -> None:
    cfg = ReplayConfig(max_snapshots=3)
    seen: List[MetricSnapshot] = []
    result = replay_history(populated_history, seen.append, cfg, _sleep=_no_sleep)
    assert result.replayed == 3
    assert result.skipped == 7


def test_metric_names_filter(populated_history: MetricHistory) -> None:
    cfg = ReplayConfig(metric_names=["error_rate"])
    seen: List[MetricSnapshot] = []
    replay_history(populated_history, seen.append, cfg, _sleep=_no_sleep)
    assert all(s.metric.name == "error_rate" for s in seen)
    assert len(seen) == 5


def test_sleep_called_with_scaled_gap() -> None:
    h = MetricHistory()
    base = 1_000_000.0
    _add(h, "cpu", 1.0, base)
    _add(h, "cpu", 2.0, base + 10.0)  # 10-second gap

    slept: List[float] = []
    cfg = ReplayConfig(speed_factor=2.0)
    replay_history(h, lambda s: None, cfg, _sleep=slept.append)
    # gap = 10 / 2.0 = 5.0 seconds
    assert slept == [5.0]


def test_empty_history_returns_zero_replayed() -> None:
    h = MetricHistory()
    result = replay_history(h, lambda s: None, _sleep=_no_sleep)
    assert result.replayed == 0
    assert result.metrics_seen == []


def test_replay_config_str() -> None:
    cfg = ReplayConfig(speed_factor=4.0, max_snapshots=100, metric_names=["a", "b"])
    s = str(cfg)
    assert "4.0x" in s
    assert "a, b" in s
    assert "100" in s


def test_replay_result_str() -> None:
    r = ReplayResult(replayed=8, skipped=2, metrics_seen=["x"])
    s = str(r)
    assert "8" in s
    assert "2" in s
