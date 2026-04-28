"""Health scoring: compute a normalized 0-100 score for each metric based on
its recent history and threshold rule evaluations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class ScoredMetric:
    metric_name: str
    score: float          # 0 (worst) – 100 (best)
    ok_ratio: float       # fraction of samples that were OK
    warning_ratio: float
    critical_ratio: float
    sample_count: int

    def __str__(self) -> str:
        return (
            f"{self.metric_name}: score={self.score:.1f} "
            f"(ok={self.ok_ratio:.0%}, warn={self.warning_ratio:.0%}, "
            f"crit={self.critical_ratio:.0%}, n={self.sample_count})"
        )


def _status_weight(status: MetricStatus) -> float:
    """Return a 0-1 contribution weight for a single sample."""
    if status == MetricStatus.OK:
        return 1.0
    if status == MetricStatus.WARNING:
        return 0.5
    return 0.0  # CRITICAL or UNKNOWN


def score_metric(
    history: MetricHistory,
    metric_name: str,
) -> Optional[ScoredMetric]:
    """Compute a health score for *metric_name* using all recorded snapshots."""
    snaps = history.snapshots(metric_name)
    if not snaps:
        return None

    total = len(snaps)
    ok = sum(1 for s in snaps if s.metric.status == MetricStatus.OK)
    warn = sum(1 for s in snaps if s.metric.status == MetricStatus.WARNING)
    crit = total - ok - warn

    score = 100.0 * sum(_status_weight(s.metric.status) for s in snaps) / total

    return ScoredMetric(
        metric_name=metric_name,
        score=round(score, 2),
        ok_ratio=ok / total,
        warning_ratio=warn / total,
        critical_ratio=crit / total,
        sample_count=total,
    )


def score_all(history: MetricHistory) -> list[ScoredMetric]:
    """Return a ScoredMetric for every metric in *history*, sorted by score ascending."""
    results = [
        score_metric(history, name)
        for name in history.metric_names()
    ]
    scored = [r for r in results if r is not None]
    scored.sort(key=lambda r: r.score)
    return scored
