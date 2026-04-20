"""Metric ranking: sort and rank metrics by value, deviation, or alert severity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class RankedMetric:
    """A metric with its computed rank score and latest value."""

    name: str
    latest_value: float
    status: MetricStatus
    sample_count: int
    rank: int

    def __str__(self) -> str:
        return (
            f"#{self.rank} {self.name}: {self.latest_value:.4f} "
            f"[{self.status.value}] ({self.sample_count} samples)\n_STATUS_WEIGHT = {
    MetricStatus.CRITICAL: 3,
    MetricStatus.WARNING: 2,
    MetricStatus.OK: 1,
    MetricStatus.UNKNOWN: 0,
}


def rank_by_value(history: MetricHistory, descending: bool = True) -> List[RankedMetric]:
    """Rank metrics by their latest recorded value."""
    entries: List[tuple[str, float, MetricStatus, int]] = []

    for name in history.metric_names():
        snapshot = history.latest(name)
        if snapshot is None:
            continue
        count = len(history.snapshots(name))
        entries.append((name, snapshot.metric.value, snapshot.metric.status, count))

    entries.sort(key=lambda e: e[1], reverse=descending)

    return [
        RankedMetric(name=e[0], latest_value=e[1], status=e[2], sample_count=e[3], rank=i + 1)
        for i, e in enumerate(entries)
    ]


def rank_by_severity(history: MetricHistory) -> List[RankedMetric]:
    """Rank metrics by alert severity (CRITICAL first), then by value descending."""
    entries: List[tuple[str, float, MetricStatus, int]] = []

    for name in history.metric_names():
        snapshot = history.latest(name)
        if snapshot is None:
            continue
        count = len(history.snapshots(name))
        entries.append((name, snapshot.metric.value, snapshot.metric.status, count))

    entries.sort(
        key=lambda e: (_STATUS_WEIGHT[e[2]], e[1]),
        reverse=True,
    )

    return [
        RankedMetric(name=e[0], latest_value=e[1], status=e[2], sample_count=e[3], rank=i + 1)
        for i, e in enumerate(entries)
    ]


def top_n(ranked: List[RankedMetric], n: int) -> List[RankedMetric]:
    """Return the top N ranked metrics."""
    return ranked[:n]
