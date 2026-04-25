"""Lossy time-series compression using the Largest-Triangle-Three-Buckets (LTTB) algorithm."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class CompressedSeries:
    metric_name: str
    original_count: int
    compressed_count: int
    snapshots: List[MetricSnapshot]

    def __str__(self) -> str:
        ratio = (
            self.compressed_count / self.original_count * 100
            if self.original_count
            else 0.0
        )
        return (
            f"CompressedSeries({self.metric_name!r}: "
            f"{self.original_count} -> {self.compressed_count} "
            f"samples, {ratio:.1f}% retained)"
        )


def _lttb(snapshots: List[MetricSnapshot], threshold: int) -> List[MetricSnapshot]:
    """Downsample *snapshots* to at most *threshold* points using LTTB."""
    n = len(snapshots)
    if threshold >= n or threshold < 3:
        return list(snapshots)

    result: List[MetricSnapshot] = [snapshots[0]]
    bucket_size = (n - 2) / (threshold - 2)
    a = 0

    for i in range(threshold - 2):
        avg_start = int((i + 1) * bucket_size) + 1
        avg_end = int((i + 2) * bucket_size) + 1
        avg_end = min(avg_end, n)
        avg_x = sum(range(avg_start, avg_end)) / (avg_end - avg_start)
        avg_y = sum(s.metric.value for s in snapshots[avg_start:avg_end]) / (
            avg_end - avg_start
        )

        range_start = int(i * bucket_size) + 1
        range_end = int((i + 1) * bucket_size) + 1
        range_end = min(range_end, n)

        max_area = -1.0
        next_a = range_start
        ax = float(a)
        ay = snapshots[a].metric.value

        for j in range(range_start, range_end):
            area = abs(
                (ax - avg_x) * (snapshots[j].metric.value - ay)
                - (ax - j) * (avg_y - ay)
            )
            if area > max_area:
                max_area = area
                next_a = j

        result.append(snapshots[next_a])
        a = next_a

    result.append(snapshots[-1])
    return result


def compress_metric(
    history: MetricHistory, metric_name: str, threshold: int = 50
) -> Optional[CompressedSeries]:
    """Compress a single metric's history to *threshold* samples."""
    snaps = history.snapshots(metric_name)
    if not snaps:
        return None
    compressed = _lttb(snaps, threshold)
    return CompressedSeries(
        metric_name=metric_name,
        original_count=len(snaps),
        compressed_count=len(compressed),
        snapshots=compressed,
    )


def compress_all(
    history: MetricHistory, threshold: int = 50
) -> List[CompressedSeries]:
    """Compress every metric tracked in *history*."""
    return [
        r
        for name in history.metric_names()
        if (r := compress_metric(history, name, threshold)) is not None
    ]
