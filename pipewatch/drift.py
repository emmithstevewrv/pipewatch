"""Metric drift detection — compare recent values against a historical baseline window.

Drift measures how much a metric's recent behaviour has shifted relative to
an earlier reference period, using mean and standard-deviation distance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
import math

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class DriftResult:
    """Drift analysis result for a single metric."""

    metric_name: str
    reference_mean: float
    reference_std: float
    recent_mean: float
    z_score: float          # how many std-devs the recent mean is from the reference mean
    drifted: bool
    threshold: float        # z-score threshold used
    reference_n: int
    recent_n: int

    def __str__(self) -> str:  # noqa: D105
        direction = "higher" if self.recent_mean > self.reference_mean else "lower"
        status = f"DRIFT ({direction})" if self.drifted else "stable"
        return (
            f"{self.metric_name}: {status}  "
            f"ref_mean={self.reference_mean:.3f} "
            f"recent_mean={self.recent_mean:.3f} "
            f"z={self.z_score:.2f}"
        )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def detect_drift(
    history: MetricHistory,
    metric_name: str,
    reference_window: int = 30,
    recent_window: int = 10,
    z_threshold: float = 2.0,
) -> Optional[DriftResult]:
    """Detect drift for a single metric.

    The oldest *reference_window* samples form the reference distribution;
    the newest *recent_window* samples are compared against it.

    Returns ``None`` when there are insufficient samples.
    """
    all_snapshots = history.snapshots(metric_name)
    min_required = reference_window + recent_window
    if len(all_snapshots) < min_required:
        return None

    reference_values = [s.value for s in all_snapshots[:reference_window]]
    recent_values = [s.value for s in all_snapshots[-recent_window:]]

    ref_mean = _mean(reference_values)
    ref_std = _std(reference_values, ref_mean)
    recent_mean = _mean(recent_values)

    if ref_std == 0.0:
        # No variance in reference — any change counts as drift
        z_score = 0.0 if recent_mean == ref_mean else float("inf")
    else:
        z_score = abs(recent_mean - ref_mean) / ref_std

    return DriftResult(
        metric_name=metric_name,
        reference_mean=ref_mean,
        reference_std=ref_std,
        recent_mean=recent_mean,
        z_score=z_score,
        drifted=z_score >= z_threshold,
        threshold=z_threshold,
        reference_n=len(reference_values),
        recent_n=len(recent_values),
    )


def detect_all_drift(
    history: MetricHistory,
    reference_window: int = 30,
    recent_window: int = 10,
    z_threshold: float = 2.0,
) -> List[DriftResult]:
    """Run drift detection across every metric tracked in *history*.

    Metrics with insufficient samples are silently skipped.
    """
    results: List[DriftResult] = []
    for name in history.metric_names():
        result = detect_drift(
            history,
            name,
            reference_window=reference_window,
            recent_window=recent_window,
            z_threshold=z_threshold,
        )
        if result is not None:
            results.append(result)
    return results
