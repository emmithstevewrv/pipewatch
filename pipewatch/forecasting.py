"""Simple linear forecasting for metric values using historical data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class ForecastResult:
    metric_name: str
    horizon: int  # steps ahead
    predicted_value: float
    slope: float
    intercept: float
    sample_count: int

    def __str__(self) -> str:
        direction = "rising" if self.slope > 0 else "falling" if self.slope < 0 else "flat"
        return (
            f"Forecast({self.metric_name}, +{self.horizon} steps): "
            f"{self.predicted_value:.4f} [{direction}, slope={self.slope:.4f}]"
        )


def _linear_regression(values: list[float]) -> tuple[float, float]:
    """Return (slope, intercept) for a simple OLS fit over index positions."""
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = num / den if den != 0 else 0.0
    intercept = mean_y - slope * mean_x
    return slope, intercept


def forecast_metric(
    history: MetricHistory,
    metric: Metric,
    horizon: int = 1,
    min_samples: int = 5,
) -> Optional[ForecastResult]:
    """Forecast the next *horizon* value(s) for a metric using linear regression.

    Args:
        history: The MetricHistory instance containing recorded values.
        metric: The metric to forecast.
        horizon: Number of steps ahead to predict. Must be >= 1.
        min_samples: Minimum number of recorded values required to produce a
            forecast. Returns None if fewer samples are available.

    Returns:
        A ForecastResult, or None if there is insufficient data.

    Raises:
        ValueError: If horizon is less than 1.
    """
    if horizon < 1:
        raise ValueError(f"horizon must be >= 1, got {horizon}")
    values = history.values(metric.name)
    if len(values) < min_samples:
        return None
    slope, intercept = _linear_regression(values)
    next_x = len(values) - 1 + horizon
    predicted = slope * next_x + intercept
    return ForecastResult(
        metric_name=metric.name,
        horizon=horizon,
        predicted_value=predicted,
        slope=slope,
        intercept=intercept,
        sample_count=len(values),
    )


def forecast_all(
    history: MetricHistory,
    horizon: int = 1,
    min_samples: int = 5,
) -> list[ForecastResult]:
    """Run forecasting for every metric tracked in history."""
    results = []
    for name in history.metric_names():
        dummy = type("_M", (), {"name": name})()
        result = forecast_metric(history, dummy, horizon=horizon, min_samples=min_samples)  # type: ignore[arg-type]
        if result is not None:
            results.append(result)
    return results
