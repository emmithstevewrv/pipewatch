"""Normalize metric values to a 0-1 scale using min-max or z-score methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pipewatch.history import MetricHistory


@dataclass
class NormalizedSeries:
    metric_name: str
    method: Literal["minmax", "zscore"]
    values: list[float]

    def __str__(self) -> str:
        return (
            f"NormalizedSeries({self.metric_name!r}, method={self.method}, "
            f"n={len(self.values)})"
        )


def _minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _zscore(values: list[float]) -> list[float]:
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = variance ** 0.5
    if std == 0.0:
        return [0.0] * n
    return [(v - mean) / std for v in values]


def normalize_metric(
    history: MetricHistory,
    metric_name: str,
    method: Literal["minmax", "zscore"] = "minmax",
    min_samples: int = 2,
) -> NormalizedSeries | None:
    values = history.values(metric_name)
    if len(values) < min_samples:
        return None
    normalized = _minmax(values) if method == "minmax" else _zscore(values)
    return NormalizedSeries(metric_name=metric_name, method=method, values=normalized)


def normalize_all(
    history: MetricHistory,
    method: Literal["minmax", "zscore"] = "minmax",
    min_samples: int = 2,
) -> dict[str, NormalizedSeries]:
    results: dict[str, NormalizedSeries] = {}
    for name in history.metric_names():
        result = normalize_metric(history, name, method=method, min_samples=min_samples)
        if result is not None:
            results[name] = result
    return results
