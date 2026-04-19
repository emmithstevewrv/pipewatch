"""Metric history storage and trend analysis."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional

from pipewatch.metrics import Metric


@dataclass
class MetricSnapshot:
    metric: Metric
    recorded_at: datetime = field(default_factory=datetime.utcnow)


class MetricHistory:
    """Stores a rolling window of metric snapshots per metric name."""

    def __init__(self, maxlen: int = 100) -> None:
        self._maxlen = maxlen
        self._store: Dict[str, Deque[MetricSnapshot]] = {}

    def record(self, metric: Metric) -> None:
        if metric.name not in self._store:
            self._store[metric.name] = deque(maxlen=self._maxlen)
        self._store[metric.name].append(MetricSnapshot(metric=metric))

    def snapshots(self, name: str) -> List[MetricSnapshot]:
        return list(self._store.get(name, []))

    def values(self, name: str) -> List[float]:
        return [s.metric.value for s in self.snapshots(name)]

    def trend(self, name: str) -> Optional[float]:
        """Return the slope (change per step) over the recorded values, or None."""
        vals = self.values(name)
        if len(vals) < 2:
            return None
        n = len(vals)
        mean_x = (n - 1) / 2
        mean_y = sum(vals) / n
        num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(vals))
        den = sum((i - mean_x) ** 2 for i in range(n))
        return num / den if den != 0 else 0.0

    def latest(self, name: str) -> Optional[MetricSnapshot]:
        snaps = self._store.get(name)
        return snaps[-1] if snaps else None

    def known_metrics(self) -> List[str]:
        return list(self._store.keys())
