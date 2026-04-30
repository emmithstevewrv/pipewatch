"""Outlier detection using IQR (interquartile range) fencing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory


@dataclass
class OutlierResult:
    metric_name: str
    value: float
    lower_fence: float
    upper_fence: float
    is_outlier: bool
    direction: str  # "high", "low", or "none"

    def __str__(self) -> str:
        if not self.is_outlier:
            return f"{self.metric_name}: no outlier (value={self.value:.4f})"
        return (
            f"{self.metric_name}: OUTLIER {self.direction} "
            f"(value={self.value:.4f}, fences=[{self.lower_fence:.4f}, {self.upper_fence:.4f}])"
        )


def _iqr_fences(values: List[float], multiplier: float = 1.5):
    """Return (lower_fence, upper_fence) using IQR method."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[(3 * n) // 4]
    iqr = q3 - q1
    return q1 - multiplier * iqr, q3 + multiplier * iqr


def detect_outlier(
    history: MetricHistory,
    metric_name: str,
    multiplier: float = 1.5,
    min_samples: int = 8,
) -> Optional[OutlierResult]:
    """Detect whether the latest value for *metric_name* is an IQR outlier."""
    values = history.values(metric_name)
    if len(values) < min_samples:
        return None

    latest = values[-1]
    lower, upper = _iqr_fences(values[:-1], multiplier)

    if latest < lower:
        direction = "low"
        is_outlier = True
    elif latest > upper:
        direction = "high"
        is_outlier = True
    else:
        direction = "none"
        is_outlier = False

    return OutlierResult(
        metric_name=metric_name,
        value=latest,
        lower_fence=lower,
        upper_fence=upper,
        is_outlier=is_outlier,
        direction=direction,
    )


def detect_all_outliers(
    history: MetricHistory,
    multiplier: float = 1.5,
    min_samples: int = 8,
) -> List[OutlierResult]:
    """Run outlier detection for every metric tracked in *history*."""
    results = []
    for name in history.metric_names():
        result = detect_outlier(history, name, multiplier, min_samples)
        if result is not None:
            results.append(result)
    return results
