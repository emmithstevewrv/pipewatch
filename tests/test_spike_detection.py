"""Tests for pipewatch.spike_detection."""

from __future__ import annotations

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.spike_detection import SpikeEvent, detect_all_spikes, detect_spike


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


@pytest.fixture()
def history() -> MetricHistory:
    return MetricHistory()


def test_returns_none_when_too_few_samples(history: MetricHistory) -> None:
    history.record(make_metric("cpu", 10.0))
    assert detect_spike(history, "cpu") is None


def test_returns_none_for_unknown_metric(history: MetricHistory) -> None:
    assert detect_spike(history, "nonexistent") is None


def test_no_spike_for_stable_values(history: MetricHistory) -> None:
    history.record(make_metric("cpu", 10.0))
    history.record(make_metric("cpu", 11.0))
    result = detect_spike(history, "cpu", threshold_pct=50.0)
    assert result is None


def test_spike_detected_upward(history: MetricHistory) -> None:
    history.record(make_metric("cpu", 10.0))
    history.record(make_metric("cpu", 20.0))
    result = detect_spike(history, "cpu", threshold_pct=50.0)
    assert result is not None
    assert isinstance(result, SpikeEvent)
    assert result.delta_pct == pytest.approx(100.0)
    assert result.delta == pytest.approx(10.0)


def test_spike_detected_downward(history: MetricHistory) -> None:
    history.record(make_metric("mem", 100.0))
    history.record(make_metric("mem", 20.0))
    result = detect_spike(history, "mem", threshold_pct=50.0)
    assert result is not None
    assert result.delta_pct == pytest.approx(-80.0)


def test_spike_from_zero_baseline(history: MetricHistory) -> None:
    history.record(make_metric("errors", 0.0))
    history.record(make_metric("errors", 5.0))
    result = detect_spike(history, "errors", threshold_pct=50.0)
    assert result is not None
    assert result.delta_pct == pytest.approx(100.0)


def test_no_spike_when_both_zero(history: MetricHistory) -> None:
    history.record(make_metric("errors", 0.0))
    history.record(make_metric("errors", 0.0))
    assert detect_spike(history, "errors") is None


def test_detect_all_spikes_returns_only_spiking_metrics(history: MetricHistory) -> None:
    history.record(make_metric("cpu", 10.0))
    history.record(make_metric("cpu", 10.5))  # stable
    history.record(make_metric("disk", 50.0))
    history.record(make_metric("disk", 150.0))  # spike
    events = detect_all_spikes(history, threshold_pct=50.0)
    names = [e.metric_name for e in events]
    assert "disk" in names
    assert "cpu" not in names


def test_spike_event_str_contains_metric_name(history: MetricHistory) -> None:
    history.record(make_metric("latency", 5.0))
    history.record(make_metric("latency", 15.0))
    result = detect_spike(history, "latency", threshold_pct=50.0)
    assert result is not None
    assert "latency" in str(result)
