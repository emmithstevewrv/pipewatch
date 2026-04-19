"""Filtering utilities for metric snapshots and history queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricSnapshot


@dataclass
class MetricFilter:
    """Criteria for filtering metric snapshots."""

    name: Optional[str] = None
    status: Optional[MetricStatus] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def matches(self, snapshot: MetricSnapshot) -> bool:
        """Return True if *snapshot* satisfies all set criteria."""
        if self.name is not None and snapshot.metric.name != self.name:
            return False
        if self.status is not None and snapshot.metric.status != self.status:
            return False
        if self.min_value is not None and snapshot.metric.value < self.min_value:
            return False
        if self.max_value is not None and snapshot.metric.value > self.max_value:
            return False
        return True


def apply_filter(
    snapshots: List[MetricSnapshot],
    metric_filter: MetricFilter,
) -> List[MetricSnapshot]:
    """Return only those snapshots that match *metric_filter*."""
    return [s for s in snapshots if metric_filter.matches(s)]


def filter_by_status(
    snapshots: List[MetricSnapshot],
    status: MetricStatus,
) -> List[MetricSnapshot]:
    """Convenience wrapper: keep snapshots whose metric has *status*."""
    return apply_filter(snapshots, MetricFilter(status=status))


def filter_by_name(
    snapshots: List[MetricSnapshot],
    name: str,
) -> List[MetricSnapshot]:
    """Convenience wrapper: keep snapshots for a specific metric name."""
    return apply_filter(snapshots, MetricFilter(name=name))
