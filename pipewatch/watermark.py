"""High-watermark and low-watermark tracking for metric series."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class WatermarkEntry:
    metric_name: str
    high: float
    low: float
    high_status: MetricStatus
    low_status: MetricStatus
    sample_count: int

    def __str__(self) -> str:
        return (
            f"WatermarkEntry({self.metric_name}: "
            f"high={self.high:.4g} [{self.high_status.value}], "
            f"low={self.low:.4g} [{self.low_status.value}], "
            f"n={self.sample_count})"
        )


def compute_watermarks(
    history: MetricHistory,
    metric_name: str,
) -> Optional[WatermarkEntry]:
    """Return high/low watermarks for *metric_name* across all recorded snapshots."""
    snaps = history.snapshots(metric_name)
    if not snaps:
        return None

    high_snap = max(snaps, key=lambda s: s.metric.value)
    low_snap = min(snaps, key=lambda s: s.metric.value)

    return WatermarkEntry(
        metric_name=metric_name,
        high=high_snap.metric.value,
        low=low_snap.metric.value,
        high_status=high_snap.metric.status,
        low_status=low_snap.metric.status,
        sample_count=len(snaps),
    )


def compute_all_watermarks(history: MetricHistory) -> list[WatermarkEntry]:
    """Compute watermarks for every metric tracked in *history*."""
    results: list[WatermarkEntry] = []
    for name in history.metric_names():
        entry = compute_watermarks(history, name)
        if entry is not None:
            results.append(entry)
    results.sort(key=lambda e: e.metric_name)
    return results
