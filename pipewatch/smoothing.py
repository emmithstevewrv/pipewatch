"""Exponential moving average smoothing for metric history."""

from dataclasses import dataclass
from typing import Optional

from pipewatch.history import MetricHistory


@dataclass
class SmoothedSeries:
    metric_name: str
    alpha: float
    values: list[float]
    smoothed: list[float]

    def latest(self) -> Optional[float]:
        return self.smoothed[-1] if self.smoothed else None

    def __str__(self) -> str:
        latest = self.latest()
        val = f"{latest:.4f}" if latest is not None else "n/a"
        return f"SmoothedSeries({self.metric_name}, alpha={self.alpha}, latest={val})"


def _ema(values: list[float], alpha: float) -> list[float]:
    if not values:
        return []
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def smooth_metric(
    history: MetricHistory,
    metric_name: str,
    alpha: float = 0.3,
) -> Optional[SmoothedSeries]:
    """Apply EMA smoothing to a single metric. Returns None if insufficient data."""
    if not (0 < alpha <= 1):
        raise ValueError(f"alpha must be in (0, 1], got {alpha}")
    snaps = history.snapshots(metric_name)
    values = [s.value for s in snaps]
    if len(values) < 2:
        return None
    return SmoothedSeries(
        metric_name=metric_name,
        alpha=alpha,
        values=values,
        smoothed=_ema(values, alpha),
    )


def smooth_all(
    history: MetricHistory,
    alpha: float = 0.3,
) -> dict[str, SmoothedSeries]:
    """Smooth all metrics in history. Skips metrics with insufficient data."""
    results = {}
    for name in history.metric_names():
        result = smooth_metric(history, name, alpha)
        if result is not None:
            results[name] = result
    return results
