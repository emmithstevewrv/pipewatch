"""Time-window aggregation utilities for metric history."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class AggregationWindow:
    metric_name: str
    window_seconds: int
    count: int
    min_value: float
    max_value: float
    avg_value: float
    start: datetime
    end: datetime

    def __str__(self) -> str:
        return (
            f"{self.metric_name} [{self.window_seconds}s window] "
            f"count={self.count} min={self.min_value:.3f} "
            f"max={self.max_value:.3f} avg={self.avg_value:.3f}"
        )


def aggregate_window(
    history: MetricHistory,
    metric_name: str,
    window_seconds: int = 60,
) -> Optional[AggregationWindow]:
    """Aggregate snapshots for a metric within the last `window_seconds`."""
    snaps: List[MetricSnapshot] = history.snapshots(metric_name)
    if not snaps:
        return None

    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    recent = [s for s in snaps if s.timestamp >= cutoff]
    if not recent:
        return None

    values = [s.metric.value for s in recent]
    return AggregationWindow(
        metric_name=metric_name,
        window_seconds=window_seconds,
        count=len(values),
        min_value=min(values),
        max_value=max(values),
        avg_value=sum(values) / len(values),
        start=recent[0].timestamp,
        end=recent[-1].timestamp,
    )


def aggregate_all(
    history: MetricHistory,
    window_seconds: int = 60,
) -> List[AggregationWindow]:
    """Aggregate all tracked metrics over the given window."""
    results = []
    for name in history.metric_names():
        w = aggregate_window(history, name, window_seconds)
        if w is not None:
            results.append(w)
    return results
