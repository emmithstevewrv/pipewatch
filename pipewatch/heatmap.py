"""Heatmap: build a time-of-day × metric status frequency grid."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus

# Hours 0-23
_HOURS = list(range(24))


@dataclass
class HeatmapRow:
    """Frequency counts per hour for a single metric."""

    metric_name: str
    # counts[hour] = number of non-OK (warning+critical) snapshots in that hour
    counts: Dict[int, int] = field(default_factory=lambda: {h: 0 for h in _HOURS})
    totals: Dict[int, int] = field(default_factory=lambda: {h: 0 for h in _HOURS})

    def incident_rate(self, hour: int) -> Optional[float]:
        """Return fraction of snapshots that were non-OK for *hour*, or None."""
        total = self.totals.get(hour, 0)
        if total == 0:
            return None
        return self.counts.get(hour, 0) / total

    def peak_hour(self) -> Optional[int]:
        """Return the hour with the highest incident rate, or None."""
        rated = [(h, self.incident_rate(h)) for h in _HOURS if self.incident_rate(h) is not None]
        if not rated:
            return None
        return max(rated, key=lambda x: x[1])[0]

    def __str__(self) -> str:
        peak = self.peak_hour()
        return f"HeatmapRow({self.metric_name!r}, peak_hour={peak})"


def build_heatmap(history: MetricHistory) -> List[HeatmapRow]:
    """Build a heatmap row for every metric tracked in *history*."""
    rows: Dict[str, HeatmapRow] = {}

    for name in history.metric_names():
        row = HeatmapRow(metric_name=name)
        for snap in history.snapshots(name):
            hour = snap.timestamp.hour
            row.totals[hour] = row.totals.get(hour, 0) + 1
            if snap.status in (MetricStatus.WARNING, MetricStatus.CRITICAL):
                row.counts[hour] = row.counts.get(hour, 0) + 1
        rows[name] = row

    return list(rows.values())
