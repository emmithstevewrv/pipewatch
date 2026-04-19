"""Correlation analysis between pairs of metrics in history."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import statistics
from pipewatch.history import MetricHistory


@dataclass
class CorrelationResult:
    metric_a: str
    metric_b: str
    coefficient: float
    sample_count: int

    def __str__(self) -> str:
        direction = "positive" if self.coefficient > 0 else "negative"
        strength = (
            "strong" if abs(self.coefficient) >= 0.7
            else "moderate" if abs(self.coefficient) >= 0.4
            else "weak"
        )
        return (
            f"{self.metric_a} <-> {self.metric_b}: "
            f"{strength} {direction} correlation "
            f"(r={self.coefficient:.3f}, n={self.sample_count})"
        )


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_a = sum((x - mx) ** 2 for x in xs) ** 0.5
    den_b = sum((y - my) ** 2 for y in ys) ** 0.5
    if den_a == 0 or den_b == 0:
        return 0.0
    return num / (den_a * den_b)


def correlate(
    history: MetricHistory,
    metric_a: str,
    metric_b: str,
    min_samples: int = 5,
) -> Optional[CorrelationResult]:
    """Return Pearson correlation between two metrics, or None if insufficient data."""
    vals_a = history.values(metric_a)
    vals_b = history.values(metric_b)
    n = min(len(vals_a), len(vals_b))
    if n < min_samples:
        return None
    xs = vals_a[-n:]
    ys = vals_b[-n:]
    coeff = _pearson(xs, ys)
    return CorrelationResult(
        metric_a=metric_a,
        metric_b=metric_b,
        coefficient=round(coeff, 6),
        sample_count=n,
    )


def correlate_all(
    history: MetricHistory,
    min_samples: int = 5,
) -> list[CorrelationResult]:
    """Compute pairwise correlations for all known metrics."""
    names = list(history.known_metrics())
    results = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            r = correlate(history, names[i], names[j], min_samples)
            if r is not None:
                results.append(r)
    return results
