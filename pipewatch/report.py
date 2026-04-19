"""Generate summary reports from metric history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class MetricSummary:
    name: str
    sample_count: int
    latest_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    trend: Optional[float]
    latest_status: MetricStatus


@dataclass
class Report:
    summaries: List[MetricSummary]

    @property
    def critical_count(self) -> int:
        return sum(1 for s in self.summaries if s.latest_status == MetricStatus.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for s in self.summaries if s.latest_status == MetricStatus.WARNING)

    @property
    def ok_count(self) -> int:
        return sum(1 for s in self.summaries if s.latest_status == MetricStatus.OK)


def build_report(history: MetricHistory) -> Report:
    """Build a Report from all metrics recorded in a MetricHistory."""
    summaries: List[MetricSummary] = []

    for name in history.metric_names():
        values = history.values(name)
        snaps = history.snapshots(name)

        if not values or not snaps:
            continue

        latest_snap = snaps[-1]
        latest_status = latest_snap.metric.status

        summaries.append(
            MetricSummary(
                name=name,
                sample_count=len(values),
                latest_value=values[-1],
                min_value=min(values),
                max_value=max(values),
                avg_value=sum(values) / len(values),
                trend=history.trend(name),
                latest_status=latest_status,
            )
        )

    return Report(summaries=summaries)
