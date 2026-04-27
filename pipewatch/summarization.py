"""Summarization: produce a human-readable health digest for a MetricHistory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class MetricDigest:
    """Single-metric summary line in a health digest."""

    name: str
    sample_count: int
    latest_value: Optional[float]
    latest_status: MetricStatus
    dominant_status: MetricStatus  # most frequent status across all samples
    critical_pct: float  # 0-100
    warning_pct: float
    ok_pct: float

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{self.name}: latest={self.latest_value} ({self.latest_status.value}), "
            f"dominant={self.dominant_status.value}, "
            f"ok={self.ok_pct:.1f}% warn={self.warning_pct:.1f}% crit={self.critical_pct:.1f}%"
        )


@dataclass
class HealthDigest:
    """Aggregate digest across all tracked metrics."""

    total_metrics: int
    total_samples: int
    metrics: List[MetricDigest] = field(default_factory=list)

    @property
    def critical_metrics(self) -> List[MetricDigest]:
        return [m for m in self.metrics if m.latest_status == MetricStatus.CRITICAL]

    @property
    def warning_metrics(self) -> List[MetricDigest]:
        return [m for m in self.metrics if m.latest_status == MetricStatus.WARNING]

    @property
    def ok_metrics(self) -> List[MetricDigest]:
        return [m for m in self.metrics if m.latest_status == MetricStatus.OK]


def _dominant(counts: Dict[MetricStatus, int]) -> MetricStatus:
    if not counts:
        return MetricStatus.OK
    return max(counts, key=lambda s: counts[s])


def summarize(history: MetricHistory) -> HealthDigest:
    """Build a HealthDigest from all snapshots stored in *history*."""
    digests: List[MetricDigest] = []
    total_samples = 0

    for name in history.metric_names():
        snaps = history.snapshots(name)
        if not snaps:
            continue
        total_samples += len(snaps)

        counts: Dict[MetricStatus, int] = {s: 0 for s in MetricStatus}
        for snap in snaps:
            counts[snap.metric.status] += 1

        n = len(snaps)
        latest = snaps[-1].metric
        digests.append(
            MetricDigest(
                name=name,
                sample_count=n,
                latest_value=latest.value,
                latest_status=latest.status,
                dominant_status=_dominant(counts),
                critical_pct=100.0 * counts[MetricStatus.CRITICAL] / n,
                warning_pct=100.0 * counts[MetricStatus.WARNING] / n,
                ok_pct=100.0 * counts[MetricStatus.OK] / n,
            )
        )

    return HealthDigest(
        total_metrics=len(digests),
        total_samples=total_samples,
        metrics=digests,
    )
