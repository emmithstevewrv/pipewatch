"""Tests for pipewatch.outlier."""
from __future__ import annotations

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.outlier import detect_outlier, detect_all_outliers, OutlierResult


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="ms")


def _populate(history: MetricHistory, name: str, values: list[float]) -> None:
    for v in values:
        history.record(make_metric(name, v))


# ── too few samples ──────────────────────────────────────────────────────────

def test_returns_none_when_too_few_samples():
    h = MetricHistory()
    _populate(h, "latency", [10.0, 20.0, 15.0])
    assert detect_outlier(h, "latency", min_samples=8) is None


def test_returns_none_for_unknown_metric():
    h = MetricHistory()
    assert detect_outlier(h, "ghost", min_samples=4) is None


# ── no outlier ───────────────────────────────────────────────────────────────

def test_no_outlier_for_stable_values():
    h = MetricHistory()
    stable = [10.0, 11.0, 10.5, 10.8, 10.2, 11.1, 10.7, 10.9, 10.4]
    _populate(h, "cpu", stable)
    result = detect_outlier(h, "cpu", min_samples=8)
    assert result is not None
    assert result.is_outlier is False
    assert result.direction == "none"


# ── high outlier ─────────────────────────────────────────────────────────────

def test_high_outlier_detected():
    h = MetricHistory()
    base = [10.0] * 8
    _populate(h, "errors", base + [500.0])
    result = detect_outlier(h, "errors", min_samples=8)
    assert result is not None
    assert result.is_outlier is True
    assert result.direction == "high"
    assert result.value == pytest.approx(500.0)


# ── low outlier ──────────────────────────────────────────────────────────────

def test_low_outlier_detected():
    h = MetricHistory()
    base = [100.0] * 8
    _populate(h, "throughput", base + [-200.0])
    result = detect_outlier(h, "throughput", min_samples=8)
    assert result is not None
    assert result.is_outlier is True
    assert result.direction == "low"


# ── fences ───────────────────────────────────────────────────────────────────

def test_result_contains_fence_values():
    h = MetricHistory()
    _populate(h, "m", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    result = detect_outlier(h, "m", min_samples=8)
    assert result is not None
    assert result.lower_fence < result.upper_fence


# ── detect_all_outliers ──────────────────────────────────────────────────────

def test_detect_all_outliers_covers_all_metrics():
    h = MetricHistory()
    for name in ("alpha", "beta"):
        _populate(h, name, [10.0] * 8 + [10.5])
    results = detect_all_outliers(h, min_samples=8)
    names = {r.metric_name for r in results}
    assert "alpha" in names
    assert "beta" in names


def test_detect_all_skips_metrics_with_too_few_samples():
    h = MetricHistory()
    _populate(h, "sparse", [1.0, 2.0])
    _populate(h, "dense", [10.0] * 8 + [10.1])
    results = detect_all_outliers(h, min_samples=8)
    names = {r.metric_name for r in results}
    assert "sparse" not in names
    assert "dense" in names


# ── __str__ ──────────────────────────────────────────────────────────────────

def test_str_no_outlier():
    r = OutlierResult("m", 5.0, 1.0, 9.0, False, "none")
    assert "no outlier" in str(r)


def test_str_outlier_includes_direction():
    r = OutlierResult("m", 999.0, 1.0, 9.0, True, "high")
    assert "OUTLIER" in str(r)
    assert "high" in str(r)
