"""Rule-based alert suppression and escalation for pipewatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory


@dataclass
class EscalationRule:
    """Escalate an alert after *consecutive* threshold breaches."""

    metric_name: str
    min_consecutive: int = 3
    suppress_ok: bool = True  # suppress alerts when status returns to OK

    def __str__(self) -> str:
        return (
            f"EscalationRule({self.metric_name!r}, "
            f"min_consecutive={self.min_consecutive})"
        )


@dataclass
class EscalationResult:
    """Result of evaluating an escalation rule against recent history."""

    metric_name: str
    should_alert: bool
    consecutive_count: int
    current_status: MetricStatus
    rule: EscalationRule

    def __str__(self) -> str:
        flag = "ALERT" if self.should_alert else "suppressed"
        return (
            f"[{flag}] {self.metric_name} — "
            f"status={self.current_status.value} "
            f"consecutive={self.consecutive_count}"
        )


def evaluate_escalation(
    rule: EscalationRule,
    history: MetricHistory,
) -> Optional[EscalationResult]:
    """Return an EscalationResult, or None if there is no history."""
    snaps = history.snapshots(rule.metric_name)
    if not snaps:
        return None

    current_status = snaps[-1].metric.status

    if rule.suppress_ok and current_status == MetricStatus.OK:
        return EscalationResult(
            metric_name=rule.metric_name,
            should_alert=False,
            consecutive_count=0,
            current_status=current_status,
            rule=rule,
        )

    # Count trailing consecutive non-OK statuses
    count = 0
    for snap in reversed(snaps):
        if snap.metric.status != MetricStatus.OK:
            count += 1
        else:
            break

    should_alert = count >= rule.min_consecutive
    return EscalationResult(
        metric_name=rule.metric_name,
        should_alert=should_alert,
        consecutive_count=count,
        current_status=current_status,
        rule=rule,
    )


def evaluate_all_escalations(
    rules: List[EscalationRule],
    history: MetricHistory,
) -> List[EscalationResult]:
    """Evaluate every rule and return only those with results."""
    results: List[EscalationResult] = []
    for rule in rules:
        result = evaluate_escalation(rule, history)
        if result is not None:
            results.append(result)
    return results
