"""Deduplication of metric snapshots based on value and time proximity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class DeduplicationPolicy:
    """Policy controlling how duplicate snapshots are identified and removed."""

    time_window: timedelta = timedelta(seconds=60)
    value_tolerance: float = 0.0

    def __str__(self) -> str:
        return (
            f"DeduplicationPolicy(window={self.time_window.total_seconds()}s, "
            f"tolerance={self.value_tolerance})"
        )


def _are_duplicates(
    a: MetricSnapshot,
    b: MetricSnapshot,
    policy: DeduplicationPolicy,
) -> bool:
    """Return True if two snapshots are considered duplicates under the given policy."""
    time_diff = abs((b.recorded_at - a.recorded_at).total_seconds())
    if time_diff > policy.time_window.total_seconds():
        return False
    value_diff = abs(b.metric.value - a.metric.value)
    return value_diff <= policy.value_tolerance


def deduplicate_series(
    snapshots: List[MetricSnapshot],
    policy: Optional[DeduplicationPolicy] = None,
) -> List[MetricSnapshot]:
    """Return a deduplicated list of snapshots, keeping the first of each duplicate run."""
    if policy is None:
        policy = DeduplicationPolicy()
    if not snapshots:
        return []
    result: List[MetricSnapshot] = [snapshots[0]]
    for snap in snapshots[1:]:
        if not _are_duplicates(result[-1], snap, policy):
            result.append(snap)
    return result


def deduplicate_history(
    history: MetricHistory,
    policy: Optional[DeduplicationPolicy] = None,
) -> dict[str, List[MetricSnapshot]]:
    """Deduplicate all metric series in a MetricHistory.

    Returns a mapping of metric_name -> deduplicated snapshot list.
    """
    if policy is None:
        policy = DeduplicationPolicy()
    result: dict[str, List[MetricSnapshot]] = {}
    for name in history.metric_names():
        snaps = history.snapshots(name)
        result[name] = deduplicate_series(snaps, policy)
    return result
