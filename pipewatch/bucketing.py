"""Value bucketing: group metric snapshots into discrete value buckets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class Bucket:
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
        return sum(s.metric.value for s in self.snapshots) / len(self.snapshots)

    def __str__(self) -> str:
        mean_str = f"{self.mean:.3f}" if self.mean is not None else "n/a"
        return f"Bucket({self.label!r}, count={self.count}, mean={mean_str})"


def bucket_metric(
    history: MetricHistory,
    metric_name: str,
    num_buckets: int = 5,
) -> Optional[List[Bucket]]:
    """Divide a metric's value range into *num_buckets* equal-width buckets."""
    snaps = history.snapshots(metric_name)
    if not snaps:
        return None

    values = [s.metric.value for s in snaps]
    lo, hi = min(values), max(values)

    if lo == hi:
        # All values identical — single bucket covers everything.
        bucket = Bucket(label=f"{lo:.3f}", low=lo, high=hi, snapshots=list(snaps))
        return [bucket]

    width = (hi - lo) / num_buckets
    buckets: List[Bucket] = []
    for i in range(num_buckets):
        low = lo + i * width
        high = lo + (i + 1) * width
        label = f"{low:.3f}–{high:.3f}"
        buckets.append(Bucket(label=label, low=low, high=high))

    for snap in snaps:
        v = snap.metric.value
        idx = min(int((v - lo) / width), num_buckets - 1)
        buckets[idx].snapshots.append(snap)

    return buckets


def bucket_all(
    history: MetricHistory,
    num_buckets: int = 5,
) -> dict[str, List[Bucket]]:
    """Run :func:`bucket_metric` for every metric in *history*."""
    result: dict[str, List[Bucket]] = {}
    for name in history.metric_names():
        buckets = bucket_metric(history, name, num_buckets=num_buckets)
        if buckets is not None:
            result[name] = buckets
    return result
