"""Alert throttling: suppress repeated alerts for the same metric within a cooldown window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class ThrottlePolicy:
    """Configuration for alert throttling."""

    cooldown_seconds: float = 300.0
    suppress_ok: bool = True

    def __str__(self) -> str:
        return f"ThrottlePolicy(cooldown={self.cooldown_seconds}s, suppress_ok={self.suppress_ok})"


@dataclass
class ThrottleState:
    """Runtime state tracked per metric name."""

    last_alerted_at: datetime
    last_status: MetricStatus
    suppressed_count: int = 0


@dataclass
class ThrottleResult:
    """Result of a throttle check for a single metric."""

    metric_name: str
    allowed: bool
    reason: str
    suppressed_count: int = 0

    def __str__(self) -> str:
        status = "allowed" if self.allowed else "suppressed"
        return f"ThrottleResult({self.metric_name}: {status} — {self.reason})"


class AlertThrottler:
    """Tracks per-metric alert state and enforces cooldown windows."""

    def __init__(self, policy: Optional[ThrottlePolicy] = None) -> None:
        self.policy: ThrottlePolicy = policy or ThrottlePolicy()
        self._state: Dict[str, ThrottleState] = {}

    def check(self, metric_name: str, status: MetricStatus, now: Optional[datetime] = None) -> ThrottleResult:
        """Determine whether an alert for *metric_name* should be sent."""
        now = now or datetime.utcnow()

        if self.policy.suppress_ok and status == MetricStatus.OK:
            return ThrottleResult(metric_name, allowed=False, reason="status is OK and suppress_ok=True")

        state = self._state.get(metric_name)
        if state is None:
            self._state[metric_name] = ThrottleState(last_alerted_at=now, last_status=status)
            return ThrottleResult(metric_name, allowed=True, reason="first alert for metric")

        elapsed = (now - state.last_alerted_at).total_seconds()
        if elapsed < self.policy.cooldown_seconds:
            state.suppressed_count += 1
            return ThrottleResult(
                metric_name,
                allowed=False,
                reason=f"cooldown active ({elapsed:.1f}s < {self.policy.cooldown_seconds}s)",
                suppressed_count=state.suppressed_count,
            )

        state.last_alerted_at = now
        state.last_status = status
        state.suppressed_count = 0
        return ThrottleResult(metric_name, allowed=True, reason="cooldown expired")

    def reset(self, metric_name: str) -> None:
        """Clear throttle state for a specific metric."""
        self._state.pop(metric_name, None)

    def reset_all(self) -> None:
        """Clear all throttle state."""
        self._state.clear()
