"""Sliding window computations over metric history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class WindowStats:
    """Statistics computed over a sliding time window."""

    metric_name: str
    window_seconds: float
    sample_count: int
    mean: Optional[float]
    std_dev: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    start: Optional[datetime]
    end: Optional[datetime]

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"WindowStats({self.metric_name}, "
            f"n={self.sample_count}, "
            f"mean={self.mean:.3f}" if self.mean is not None else "mean=None"
            f")"
        )


def compute_window(
    history: MetricHistory,
    metric_name: str,
    window_seconds: float,
    reference_time: Optional[datetime] = None,
) -> Optional[WindowStats]:
    """Return statistics for *metric_name* over the last *window_seconds*.

    Returns ``None`` if the metric has no recorded snapshots.
    """
    all_snaps: List[MetricSnapshot] = history.snapshots(metric_name)
    if not all_snaps:
        return None

    ref = reference_time or datetime.utcnow()
    cutoff = ref - timedelta(seconds=window_seconds)
    window_snaps = [s for s in all_snaps if s.timestamp >= cutoff]

    values = [s.metric.value for s in window_snaps if s.metric.value is not None]
    n = len(values)

    return WindowStats(
        metric_name=metric_name,
        window_seconds=window_seconds,
        sample_count=n,
        mean=mean(values) if n else None,
        std_dev=stdev(values) if n >= 2 else None,
        min_value=min(values) if n else None,
        max_value=max(values) if n else None,
        start=window_snaps[0].timestamp if window_snaps else None,
        end=window_snaps[-1].timestamp if window_snaps else None,
    )


def compute_all_windows(
    history: MetricHistory,
    window_seconds: float,
    reference_time: Optional[datetime] = None,
) -> List[WindowStats]:
    """Compute window statistics for every tracked metric."""
    results = []
    for name in history.metric_names():
        stat = compute_window(history, name, window_seconds, reference_time)
        if stat is not None:
            results.append(stat)
    return results
