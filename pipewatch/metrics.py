"""Core metric models for pipeline health tracking."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict = field(default_factory=dict)
    status: MetricStatus = MetricStatus.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "status": self.status.value,
        }


@dataclass
class ThresholdRule:
    metric_name: str
    warning_above: Optional[float] = None
    critical_above: Optional[float] = None
    warning_below: Optional[float] = None
    critical_below: Optional[float] = None

    def evaluate(self, metric: Metric) -> MetricStatus:
        v = metric.value
        if self.critical_above is not None and v > self.critical_above:
            return MetricStatus.CRITICAL
        if self.critical_below is not None and v < self.critical_below:
            return MetricStatus.CRITICAL
        if self.warning_above is not None and v > self.warning_above:
            return MetricStatus.WARNING
        if self.warning_below is not None and v < self.warning_below:
            return MetricStatus.WARNING
        return MetricStatus.OK
