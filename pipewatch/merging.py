"""Merge multiple MetricHistory instances into a unified view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class MergeResult:
    """Unified history produced by merging two or more MetricHistory objects."""

    metric_names: List[str]
    snapshots: Dict[str, List[MetricSnapshot]] = field(default_factory=dict)
    conflicts: int = 0  # duplicate timestamps resolved during merge

    def __str__(self) -> str:
        total = sum(len(v) for v in self.snapshots.values())
        return (
            f"MergeResult(metrics={len(self.metric_names)}, "
            f"total_snapshots={total}, conflicts={self.conflicts})"
        )

    def latest(self, metric_name: str) -> Optional[MetricSnapshot]:
        """Return the most recent snapshot for *metric_name*, or None."""
        snaps = self.snapshots.get(metric_name)
        if not snaps:
            return None
        return max(snaps, key=lambda s: s.timestamp)


def _merge_series(
    series_a: List[MetricSnapshot],
    series_b: List[MetricSnapshot],
) -> tuple[List[MetricSnapshot], int]:
    """Merge two snapshot lists, deduplicating by timestamp.

    When two snapshots share the same timestamp the one from *series_b*
    (the later source) wins.  Returns the merged list and a conflict count.
    """
    by_ts: Dict[float, MetricSnapshot] = {}
    conflicts = 0
    for snap in series_a:
        by_ts[snap.timestamp] = snap
    for snap in series_b:
        if snap.timestamp in by_ts:
            conflicts += 1
        by_ts[snap.timestamp] = snap
    merged = sorted(by_ts.values(), key=lambda s: s.timestamp)
    return merged, conflicts


def merge_histories(*histories: MetricHistory) -> MergeResult:
    """Merge an arbitrary number of :class:`MetricHistory` objects.

    Snapshots for each metric are combined across all sources and sorted
    chronologically.  Duplicate timestamps (same metric, same timestamp)
    are resolved by keeping the entry from the *later* history argument.

    Parameters
    ----------
    *histories:
        One or more :class:`MetricHistory` instances to merge.

    Returns
    -------
    MergeResult
        A unified view of all metrics and their snapshots.
    """
    combined: Dict[str, List[MetricSnapshot]] = {}
    total_conflicts = 0

    for history in histories:
        for name in history.metric_names():
            incoming = history.snapshots(name)
            if name not in combined:
                combined[name] = list(incoming)
            else:
                merged, conflicts = _merge_series(combined[name], incoming)
                combined[name] = merged
                total_conflicts += conflicts

    return MergeResult(
        metric_names=sorted(combined.keys()),
        snapshots=combined,
        conflicts=total_conflicts,
    )
