"""Tests for pipewatch.alerting_rules."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.alerting_rules import (
    EscalationRule,
    EscalationResult,
    evaluate_escalation,
    evaluate_all_escalations,
)


def make_metric(name: str, status: MetricStatus, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=status, timestamp=datetime.now(timezone.utc))


def _add(history: MetricHistory, name: str, status: MetricStatus, value: float = 1.0) -> None:
    history.record(make_metric(name, status, value))


# ---------------------------------------------------------------------------
# evaluate_escalation
# ---------------------------------------------------------------------------

def test_returns_none_for_empty_history():
    history = MetricHistory()
    rule = EscalationRule(metric_name="cpu", min_consecutive=2)
    assert evaluate_escalation(rule, history) is None


def test_ok_status_suppressed_by_default():
    history = MetricHistory()
    _add(history, "cpu", MetricStatus.OK)
    rule = EscalationRule(metric_name="cpu", min_consecutive=1)
    result = evaluate_escalation(rule, history)
    assert result is not None
    assert result.should_alert is False
    assert result.consecutive_count == 0


def test_ok_status_not_suppressed_when_flag_off():
    history = MetricHistory()
    _add(history, "cpu", MetricStatus.OK)
    rule = EscalationRule(metric_name="cpu", min_consecutive=1, suppress_ok=False)
    result = evaluate_escalation(rule, history)
    assert result is not None
    # consecutive non-OK count is 0, so should_alert is False (0 < 1)
    assert result.should_alert is False


def test_single_critical_below_threshold():
    history = MetricHistory()
    _add(history, "cpu", MetricStatus.CRITICAL)
    rule = EscalationRule(metric_name="cpu", min_consecutive=3)
    result = evaluate_escalation(rule, history)
    assert result is not None
    assert result.should_alert is False
    assert result.consecutive_count == 1


def test_consecutive_critical_meets_threshold():
    history = MetricHistory()
    for _ in range(3):
        _add(history, "cpu", MetricStatus.CRITICAL)
    rule = EscalationRule(metric_name="cpu", min_consecutive=3)
    result = evaluate_escalation(rule, history)
    assert result is not None
    assert result.should_alert is True
    assert result.consecutive_count == 3


def test_ok_resets_consecutive_count():
    history = MetricHistory()
    _add(history, "cpu", MetricStatus.CRITICAL)
    _add(history, "cpu", MetricStatus.CRITICAL)
    _add(history, "cpu", MetricStatus.OK)       # reset
    _add(history, "cpu", MetricStatus.CRITICAL)  # only 1 after reset
    rule = EscalationRule(metric_name="cpu", min_consecutive=2, suppress_ok=False)
    result = evaluate_escalation(rule, history)
    assert result is not None
    assert result.consecutive_count == 1
    assert result.should_alert is False


def test_warning_counts_as_non_ok():
    history = MetricHistory()
    for _ in range(2):
        _add(history, "mem", MetricStatus.WARNING)
    rule = EscalationRule(metric_name="mem", min_consecutive=2)
    result = evaluate_escalation(rule, history)
    assert result is not None
    assert result.should_alert is True


# ---------------------------------------------------------------------------
# evaluate_all_escalations
# ---------------------------------------------------------------------------

def test_evaluate_all_skips_missing_metrics():
    history = MetricHistory()
    _add(history, "cpu", MetricStatus.CRITICAL)
    rules = [
        EscalationRule(metric_name="cpu", min_consecutive=1),
        EscalationRule(metric_name="missing", min_consecutive=1),
    ]
    results = evaluate_all_escalations(rules, history)
    assert len(results) == 1
    assert results[0].metric_name == "cpu"


def test_evaluate_all_returns_all_present_metrics():
    history = MetricHistory()
    _add(history, "cpu", MetricStatus.CRITICAL)
    _add(history, "mem", MetricStatus.WARNING)
    rules = [
        EscalationRule(metric_name="cpu", min_consecutive=1),
        EscalationRule(metric_name="mem", min_consecutive=1),
    ]
    results = evaluate_all_escalations(rules, history)
    assert len(results) == 2
