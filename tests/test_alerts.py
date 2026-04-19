"""Tests for pipewatch.alerts dispatch logic."""
from __future__ import annotations

from datetime import datetime
from typing import List
from unittest.mock import MagicMock

import pytest

from pipewatch.alerts import AlertBackend, AlertEvent, LoggingBackend, dispatch_alerts
from pipewatch.metrics import Metric, MetricStatus


def make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status, timestamp=datetime.utcnow())


class CapturingBackend(AlertBackend):
    def __init__(self):
        self.received: List[AlertEvent] = []

    def send(self, events):
        self.received.extend(events)


def test_no_alerts_for_ok_metrics():
    metrics = [make_metric("rows", 100, MetricStatus.OK)]
    backend = CapturingBackend()
    events = dispatch_alerts(metrics, [backend])
    assert events == []
    assert backend.received == []


def test_warning_metric_produces_event():
    metrics = [make_metric("latency", 5.0, MetricStatus.WARNING)]
    backend = CapturingBackend()
    events = dispatch_alerts(metrics, [backend])
    assert len(events) == 1
    assert events[0].metric.name == "latency"
    assert "warning" in str(events[0])


def test_critical_metric_produces_event():
    metrics = [make_metric("errors", 50, MetricStatus.CRITICAL)]
    backend = CapturingBackend()
    events = dispatch_alerts(metrics, [backend])
    assert len(events) == 1
    assert events[0].metric.status == MetricStatus.CRITICAL


def test_multiple_backends_all_called():
    metrics = [make_metric("errors", 50, MetricStatus.CRITICAL)]
    b1 = CapturingBackend()
    b2 = CapturingBackend()
    dispatch_alerts(metrics, [b1, b2])
    assert len(b1.received) == 1
    assert len(b2.received) == 1


def test_mixed_statuses_only_non_ok_alerted():
    metrics = [
        make_metric("a", 1, MetricStatus.OK),
        make_metric("b", 2, MetricStatus.WARNING),
        make_metric("c", 3, MetricStatus.CRITICAL),
    ]
    backend = CapturingBackend()
    events = dispatch_alerts(metrics, [backend])
    assert len(events) == 2
    names = {e.metric.name for e in events}
    assert names == {"b", "c"}


def test_logging_backend_does_not_raise(caplog):
    import logging
    metrics = [make_metric("x", 99, MetricStatus.CRITICAL)]
    backend = LoggingBackend()
    with caplog.at_level(logging.CRITICAL, logger="pipewatch.alerts"):
        dispatch_alerts(metrics, [backend])
    assert any("CRITICAL" in r.levelname for r in caplog.records)
