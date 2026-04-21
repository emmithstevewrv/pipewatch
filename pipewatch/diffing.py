"""Metric diffing: compare two snapshots or history windows and report changes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class DiffEntry:
    metric_name: str
    old_value: Optional[float]
    new_value: Optional[float]
    old_status: Optional[MetricStatus]
    new_status: Optional[MetricStatus]

    @property
    def value_delta(self) -> Optional[float]:
        if self.old_value is None or self.new_value is None:
            return None
        return self.new_value - self.old_value

    @property
    def status_changed(self) -> bool:
        return self.old_status != self.new_status

    def __str__(self) -> str:
        delta = self.value_delta
        delta_str = f"{delta:+.4g}" if delta is not None else "n/a"
        return (
            f"{self.metric_name}: {self.old_value} -> {self.new_value} "
            f"(delta={delta_str}, "
            f"status: {self.old_status} -> {self.new_status})"
        )


def diff_history(history: MetricHistory, window: int = 2) -> list[DiffEntry]:
    """Compare the latest value vs the value `window` steps ago for every metric."""
    entries: list[DiffEntry] = []
    for name in history.metric_names():
        snaps = history.snapshots(name)
        if not snaps:
            continue
        latest = snaps[-1]
        older = snaps[-window] if len(snaps) >= window else snaps[0]
        entries.append(
            DiffEntry(
                metric_name=name,
                old_value=older.metric.value,
                new_value=latest.metric.value,
                old_status=older.metric.status,
                new_status=latest.metric.status,
            )
        )
    return entries


def status_regressions(diffs: list[DiffEntry]) -> list[DiffEntry]:
    """Return only entries where the status worsened (OK->WARN or WARN->CRIT etc.)."""
    order = {MetricStatus.OK: 0, MetricStatus.WARNING: 1, MetricStatus.CRITICAL: 2}
    return [
        d for d in diffs
        if d.old_status is not None
        and d.new_status is not None
        and order.get(d.new_status, 0) > order.get(d.old_status, 0)
    ]
