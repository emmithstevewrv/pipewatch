"""High-level query helpers that combine MetricHistory with MetricFilter."""

from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.filter import MetricFilter, apply_filter


def query_history(
    history: MetricHistory,
    metric_filter: Optional[MetricFilter] = None,
) -> List[MetricSnapshot]:
    """Return all snapshots across every metric, optionally filtered."""
    all_snapshots: List[MetricSnapshot] = []
    for name in history._data:  # noqa: SLF001
        all_snapshots.extend(history.snapshots(name))
    if metric_filter is None:
        return all_snapshots
    return apply_filter(all_snapshots, metric_filter)


def critical_snapshots(history: MetricHistory) -> List[MetricSnapshot]:
    """Return all snapshots with CRITICAL status."""
    return query_history(history, MetricFilter(status=MetricStatus.CRITICAL))


def warning_snapshots(history: MetricHistory) -> List[MetricSnapshot]:
    """Return all snapshots with WARNING status."""
    return query_history(history, MetricFilter(status=MetricStatus.WARNING))


def snapshots_for_metric(
    history: MetricHistory,
    name: str,
    status: Optional[MetricStatus] = None,
) -> List[MetricSnapshot]:
    """Return snapshots for a named metric, with an optional status filter."""
    return query_history(history, MetricFilter(name=name, status=status))


def status_counts(history: MetricHistory) -> Dict[MetricStatus, int]:
    """Return a mapping of MetricStatus -> count across all recorded snapshots."""
    counts: Dict[MetricStatus, int] = {s: 0 for s in MetricStatus}
    for snapshot in query_history(history):
        counts[snapshot.metric.status] += 1
    return counts
