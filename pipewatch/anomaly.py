"""Simple anomaly detection for metric history using z-score."""

from dataclasses import dataclass
from typing import Optional

from pipewatch.history import MetricHistory


@dataclass
class AnomalyResult:
    metric_name: str
    value: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool

    def __str__(self) -> str:
        flag = "[ANOMALY]" if self.is_anomaly else "[OK]"
        return (
            f"{flag} {self.metric_name}: value={self.value:.3f} "
            f"mean={self.mean:.3f} stddev={self.stddev:.3f} z={self.z_score:.2f}"
        )


def detect_anomaly(
    history: MetricHistory,
    metric_name: str,
    threshold: float = 2.5,
    min_samples: int = 5,
) -> Optional[AnomalyResult]:
    """Return an AnomalyResult if the latest value is anomalous, else None."""
    values = history.values(metric_name)
    if len(values) < min_samples:
        return None

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    stddev = variance ** 0.5

    if stddev == 0:
        return None

    latest = values[-1]
    z_score = abs(latest - mean) / stddev
    is_anomaly = z_score >= threshold

    return AnomalyResult(
        metric_name=metric_name,
        value=latest,
        mean=mean,
        stddev=stddev,
        z_score=z_score,
        is_anomaly=is_anomaly,
    )


def detect_all_anomalies(
    history: MetricHistory,
    threshold: float = 2.5,
    min_samples: int = 5,
) -> list[AnomalyResult]:
    """Run anomaly detection across all tracked metrics."""
    results = []
    for name in history.metric_names():
        result = detect_anomaly(history, name, threshold, min_samples)
        if result is not None and result.is_anomaly:
            results.append(result)
    return results
