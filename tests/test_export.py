"""Tests for pipewatch.export."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.export import export_history


def make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture()
def populated_history() -> MetricHistory:
    h = MetricHistory()
    h.record(make_metric("rows_loaded", 100.0, MetricStatus.OK))
    h.record(make_metric("rows_loaded", 50.0, MetricStatus.WARNING))
    h.record(make_metric("error_rate", 0.05, MetricStatus.OK))
    return h


def test_json_export_returns_all_rows(populated_history):
    output = export_history(populated_history, fmt="json")
    data = json.loads(output)
    assert len(data) == 3


def test_json_export_fields(populated_history):
    data = json.loads(export_history(populated_history, fmt="json"))
    for row in data:
        assert set(row.keys()) == {"metric", "value", "status", "timestamp"}


def test_json_export_status_is_string(populated_history):
    data = json.loads(export_history(populated_history, fmt="json"))
    assert all(isinstance(row["status"], str) for row in data)


def test_csv_export_returns_all_rows(populated_history):
    output = export_history(populated_history, fmt="csv")
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 3


def test_csv_export_has_header(populated_history):
    output = export_history(populated_history, fmt="csv")
    assert output.startswith("metric,value,status,timestamp")


def test_unsupported_format_raises(populated_history):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_history(populated_history, fmt="xml")  # type: ignore[arg-type]


def test_empty_history_json():
    data = json.loads(export_history(MetricHistory(), fmt="json"))
    assert data == []


def test_empty_history_csv():
    output = export_history(MetricHistory(), fmt="csv")
    reader = csv.DictReader(io.StringIO(output))
    assert list(reader) == []
