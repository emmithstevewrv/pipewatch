"""Metric rollup: collapse a history window into a single representative snapshot per metric."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus


@dataclass
class RollupEntry:
    metric_name: str
    window_seconds: float
    sample_count: int
    avg_value: float
    min_value: float
    max_value: float
    dominant_status: MetricStatus
    rolled_at: datetime

    def __str__(self) -> str:
        return (
            f"RollupEntry({self.metric_name}, "
            f"avg={self.avg_value:.4f}, "
            f"samples={self.sample_count}, "
            f"status={self.dominant_status.value})"
        )


def _dominant_status(statuses: list[MetricStatus]) -> MetricStatus:
    """Return the most severe status present in the list."""
    if MetricStatus.CRITICAL in statuses:
        return MetricStatus.CRITICAL
    if MetricStatus.WARNING in statuses:
        return MetricStatus.WARNING
    return MetricStatus.OK


def rollup_metric(
    history: MetricHistory,
    metric_name: str,
    window_seconds: float = 60.0,
) -> Optional[RollupEntry]:
    """Collapse recent snapshots for *metric_name* into a single RollupEntry."""
    all_snapshots = history.snapshots(metric_name)
    if not all_snapshots:
        return None

    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    recent = [s for s in all_snapshots if s.recorded_at >= cutoff]
    if not recent:
        return None

    values = [s.metric.value for s in recent]
    statuses = [s.metric.status for s in recent]
    return RollupEntry(
        metric_name=metric_name,
        window_seconds=window_seconds,
        sample_count=len(recent),
        avg_value=mean(values),
        min_value=min(values),
        max_value=max(values),
        dominant_status=_dominant_status(statuses),
        rolled_at=datetime.utcnow(),
    )


def rollup_all(
    history: MetricHistory,
    window_seconds: float = 60.0,
) -> list[RollupEntry]:
    """Return a RollupEntry for every metric tracked in *history*."""
    results: list[RollupEntry] = []
    for name in history.metric_names():
        entry = rollup_metric(history, name, window_seconds)
        if entry is not None:
            results.append(entry)
    return results
