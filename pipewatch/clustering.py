"""Cluster metrics by value similarity using simple bucketing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory


@dataclass
class Cluster:
    label: str
    metric_names: List[str]
    centroid: float
    min_value: float
    max_value: float

    def __str__(self) -> str:
        names = ", ".join(self.metric_names)
        return (
            f"Cluster({self.label!r}, centroid={self.centroid:.3f}, "
            f"range=[{self.min_value:.3f}, {self.max_value:.3f}], metrics=[{names}])"
        )


def _bucket_label(index: int) -> str:
    """Return a human-readable cluster label."""
    return f"C{index + 1}"


def cluster_metrics(
    history: MetricHistory,
    n_clusters: int = 3,
    metric_names: Optional[List[str]] = None,
) -> List[Cluster]:
    """Cluster metrics by their latest mean value into *n_clusters* buckets.

    Metrics with no recorded values are silently skipped.
    Returns an empty list when fewer than 2 metrics have data.
    """
    names = metric_names if metric_names is not None else list(history._data.keys())

    averages: Dict[str, float] = {}
    for name in names:
        vals = history.values(name)
        if vals:
            averages[name] = sum(vals) / len(vals)

    if len(averages) < 2:
        return []

    sorted_names = sorted(averages, key=lambda n: averages[n])
    all_vals = [averages[n] for n in sorted_names]
    global_min, global_max = all_vals[0], all_vals[-1]
    span = global_max - global_min or 1.0

    buckets: Dict[int, List[str]] = {i: [] for i in range(n_clusters)}
    for name in sorted_names:
        idx = min(int((averages[name] - global_min) / span * n_clusters), n_clusters - 1)
        buckets[idx].append(name)

    clusters: List[Cluster] = []
    for idx, bucket_names in buckets.items():
        if not bucket_names:
            continue
        vals = [averages[n] for n in bucket_names]
        clusters.append(
            Cluster(
                label=_bucket_label(idx),
                metric_names=bucket_names,
                centroid=sum(vals) / len(vals),
                min_value=min(vals),
                max_value=max(vals),
            )
        )

    return clusters
