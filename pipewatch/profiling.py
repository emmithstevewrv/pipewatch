"""Metric profiling: compute distributional statistics for a metric's history.

A MetricProfile captures percentile breakdowns, variance, and coefficient of
variation so operators can understand the typical behaviour of a metric beyond
simple min/max/avg.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory


@dataclass
class MetricProfile:
    """Distributional profile for a single metric."""

    metric_name: str
    sample_count: int
    mean: float
    std_dev: float
    variance: float
    cv: float  # coefficient of variation (std_dev / mean), NaN when mean == 0
    p25: float
    p50: float
    p75: float
    p90: float
    p99: float
    minimum: float
    maximum: float

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"MetricProfile({self.metric_name}: "
            f"p50={self.p50:.3f}, p99={self.p99:.3f}, "
            f"cv={self.cv:.3f}, n={self.sample_count})"
        )


def _percentile(sorted_values: List[float], pct: float) -> float:
    """Return the *pct*-th percentile (0-100) using linear interpolation."""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    index = (pct / 100.0) * (n - 1)
    lower = int(index)
    upper = lower + 1
    if upper >= n:
        return sorted_values[-1]
    frac = index - lower
    return sorted_values[lower] + frac * (sorted_values[upper] - sorted_values[lower])


def profile_metric(history: MetricHistory, metric_name: str) -> Optional[MetricProfile]:
    """Build a :class:`MetricProfile` for *metric_name* from *history*.

    Returns ``None`` when the metric is unknown or has fewer than 2 samples
    (not enough data to compute meaningful statistics).
    """
    snaps = history.snapshots(metric_name)
    values = [s.metric.value for s in snaps]

    if len(values) < 2:
        return None

    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std_dev = math.sqrt(variance)
    cv = (std_dev / mean) if mean != 0.0 else float("nan")

    sv = sorted(values)

    return MetricProfile(
        metric_name=metric_name,
        sample_count=n,
        mean=mean,
        std_dev=std_dev,
        variance=variance,
        cv=cv,
        p25=_percentile(sv, 25),
        p50=_percentile(sv, 50),
        p75=_percentile(sv, 75),
        p90=_percentile(sv, 90),
        p99=_percentile(sv, 99),
        minimum=sv[0],
        maximum=sv[-1],
    )


def profile_all(history: MetricHistory) -> Dict[str, MetricProfile]:
    """Return a :class:`MetricProfile` for every metric stored in *history*.

    Metrics with insufficient data are silently omitted.
    """
    results: Dict[str, MetricProfile] = {}
    for name in history.metric_names():
        profile = profile_metric(history, name)
        if profile is not None:
            results[name] = profile
    return results
