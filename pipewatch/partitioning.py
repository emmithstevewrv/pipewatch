"""Partition metric history into named groups based on value ranges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class Partition:
    """A named bucket containing snapshots whose values fall within [low, high)."""

    label: str
    low: float
    high: float
    snapshots: List[MetricSnapshot] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.snapshots)

    @property
    def mean(self) -> Optional[float]:
        if not self.snapshots:
            return None
        return sum(s.value for s in self.snapshots) / len(self.snapshots)

    def __str__(self) -> str:
        return (
            f"Partition({self.label!r}, [{self.low}, {self.high}), "
            f"n={self.count})"
        )


def _build_partitions(
    bounds: List[Tuple[str, float, float]]
) -> List[Partition]:
    return [Partition(label=lbl, low=lo, high=hi) for lbl, lo, hi in bounds]


def partition_metric(
    history: MetricHistory,
    metric_name: str,
    bounds: List[Tuple[str, float, float]],
) -> Optional[List[Partition]]:
    """Partition snapshots for *metric_name* into buckets defined by *bounds*.

    Each bound is a ``(label, low, high)`` triple where the interval is
    ``[low, high)``.  Snapshots that fall outside every bound are ignored.
    Returns ``None`` when the metric has no recorded history.
    """
    snaps = history.snapshots(metric_name)
    if not snaps:
        return None

    partitions = _build_partitions(bounds)
    for snap in snaps:
        for part in partitions:
            if part.low <= snap.value < part.high:
                part.snapshots.append(snap)
                break
    return partitions


def partition_all(
    history: MetricHistory,
    bounds: List[Tuple[str, float, float]],
) -> Dict[str, List[Partition]]:
    """Run :func:`partition_metric` for every known metric in *history*."""
    return {
        name: result
        for name in history.metric_names()
        if (result := partition_metric(history, name, bounds)) is not None
    }
