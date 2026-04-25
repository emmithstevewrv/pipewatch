"""Tests for pipewatch.display_alerting_rules."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import List

from rich.console import Console

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.alerting_rules import EscalationRule, EscalationResult
from pipewatch.display_alerting_rules import (
    render_escalation_table,
    render_escalation_summary,
)


def _make_result(
    name: str,
    status: MetricStatus,
    consecutive: int,
    min_consec: int,
    should_alert: bool,
) -> EscalationResult:
    rule = EscalationRule(metric_name=name, min_consecutive=min_consec)
    return EscalationResult(
        metric_name=name,
        should_alert=should_alert,
        consecutive_count=consecutive,
        current_status=status,
        rule=rule,
    )


def _capture(results: List[EscalationResult], fn) -> str:
    buf = io.StringIO()
    console = Console(file=buf, highlight=False, markup=False)
    import pipewatch.display_alerting_rules as mod
    original = mod._console
    mod._console = console
    try:
        fn(results)
    finally:
        mod._console = original
    return buf.getvalue()


def test_render_table_contains_metric_names():
    results = [
        _make_result("cpu", MetricStatus.CRITICAL, 3, 3, True),
        _make_result("mem", MetricStatus.WARNING, 1, 3, False),
    ]
    output = _capture(results, render_escalation_table)
    assert "cpu" in output
    assert "mem" in output


def test_render_table_shows_consecutive_count():
    results = [_make_result("disk", MetricStatus.CRITICAL, 5, 3, True)]
    output = _capture(results, render_escalation_table)
    assert "5" in output


def test_render_summary_empty():
    output = _capture([], render_escalation_summary)
    assert "No escalation rules" in output


def test_render_summary_firing_count():
    results = [
        _make_result("cpu", MetricStatus.CRITICAL, 3, 3, True),
        _make_result("mem", MetricStatus.WARNING, 1, 3, False),
    ]
    output = _capture(results, render_escalation_summary)
    assert "1" in output   # 1 firing
    assert "2" in output   # 2 total
