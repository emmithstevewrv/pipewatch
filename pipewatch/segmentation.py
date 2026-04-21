"""Segment metric history into time-based windows for comparative analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class Segment:
    """A named slice of metric snapshots within a time window."""

    label: str
    start: datetime
    end: datetime
    snapshots: List[MetricSnapshot] = field(default_factory=list)

    @property
    def values(self) -> List[float]:
        return [s.value for s in self.snapshots]

    @property
    def mean(self) -> Optional[float]:
        if not self.values:
            return None
        return sum(self.values) / len(self.values)

    @property
    def sample_count(self) -> int:
        return len(self.snapshots)

    def __str__(self) -> str:
        mean_str = f"{self.mean:.4f}" if self.mean is not None else "n/a"
        return (
            f"Segment({self.label!r}, n={self.sample_count}, mean={mean_str})"
        )


def segment_metric(
    history: MetricHistory,
    metric_name: str,
    window_size: timedelta,
    num_windows: int,
    reference_time: Optional[datetime] = None,
) -> List[Segment]:
    """Split a metric's history into equal-sized time segments.

    Returns segments ordered from oldest to newest.
    """
    if reference_time is None:
        reference_time = datetime.utcnow()

    all_snapshots = history.snapshots(metric_name)
    segments: List[Segment] = []

    for i in range(num_windows - 1, -1, -1):
        end = reference_time - window_size * i
        start = end - window_size
        label = f"T-{i}" if i > 0 else "current"
        matching = [
            s for s in all_snapshots if start <= s.timestamp < end
        ]
        segments.append(Segment(label=label, start=start, end=end, snapshots=matching))

    return segments


def segment_all(
    history: MetricHistory,
    window_size: timedelta,
    num_windows: int,
    reference_time: Optional[datetime] = None,
) -> dict[str, List[Segment]]:
    """Segment all tracked metrics."""
    return {
        name: segment_metric(history, name, window_size, num_windows, reference_time)
        for name in history.metric_names()
    }
