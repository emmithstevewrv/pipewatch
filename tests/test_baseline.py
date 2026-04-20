"""Tests for pipewatch.baseline module."""

import json
import pytest
from pathlib import Path

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.baseline import (
    BaselineEntry,
    BaselineStore,
    BaselineResult,
    load_baseline_store,
    save_baseline_store,
)


def make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, message="ok")


@pytest.fixture
def store() -> BaselineStore:
    s = BaselineStore()
    s.add(BaselineEntry(name="row_count", expected_value=1000.0, tolerance_pct=10.0))
    s.add(BaselineEntry(name="latency_ms", expected_value=200.0, tolerance_pct=20.0))
    return s


def test_within_tolerance(store):
    m = make_metric("row_count", 1050.0)
    result = store.compare(m)
    assert result is not None
    assert result.within_tolerance
    assert pytest.approx(result.deviation_pct, rel=1e-3) == 5.0


def test_outside_tolerance(store):
    m = make_metric("row_count", 1200.0)
    result = store.compare(m)
    assert result is not None
    assert not result.within_tolerance
    assert result.deviation_pct > 10.0


def test_unknown_metric_returns_none(store):
    m = make_metric("unknown_metric", 42.0)
    assert store.compare(m) is None


def test_compare_all_filters_unknown(store):
    metrics = [
        make_metric("row_count", 1000.0),
        make_metric("unknown", 99.0),
        make_metric("latency_ms", 190.0),
    ]
    results = store.compare_all(metrics)
    assert len(results) == 2
    assert all(isinstance(r, BaselineResult) for r in results)


def test_zero_expected_value():
    entry = BaselineEntry(name="errors", expected_value=0.0, tolerance_pct=5.0)
    assert entry.deviation_pct(0.0) == 0.0
    assert entry.is_within_tolerance(0.0)


def test_str_representation(store):
    m = make_metric("row_count", 900.0)
    result = store.compare(m)
    s = str(result)
    assert "row_count" in s
    assert "DEVIATION" in s


def test_save_and_load_roundtrip(tmp_path, store):
    path = tmp_path / "baselines.json"
    save_baseline_store(store, path)
    loaded = load_baseline_store(path)
    result = loaded.compare(make_metric("row_count", 1000.0))
    assert result is not None
    assert result.within_tolerance


def test_load_from_file(tmp_path):
    data = [{"name": "throughput", "expected_value": 500.0, "tolerance_pct": 15.0}]
    p = tmp_path / "b.json"
    p.write_text(json.dumps(data))
    store = load_baseline_store(p)
    assert store.get("throughput") is not None


def test_load_missing_file_raises(tmp_path):
    """Loading a non-existent baseline file should raise FileNotFoundError."""
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        load_baseline_store(missing)
