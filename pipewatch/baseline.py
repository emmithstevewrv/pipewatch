"""Baseline comparison: compare current metric values against stored baselines."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from pipewatch.metrics import Metric


@dataclass
class BaselineEntry:
    name: str
    expected_value: float
    tolerance_pct: float = 10.0

    def deviation_pct(self, actual: float) -> float:
        if self.expected_value == 0:
            return 0.0
        return abs(actual - self.expected_value) / abs(self.expected_value) * 100

    def is_within_tolerance(self, actual: float) -> bool:
        return self.deviation_pct(actual) <= self.tolerance_pct


@dataclass
class BaselineResult:
    metric: Metric
    entry: BaselineEntry
    deviation_pct: float
    within_tolerance: bool

    def __str__(self) -> str:
        status = "OK" if self.within_tolerance else "DEVIATION"
        return (
            f"[{status}] {self.metric.name}: "
            f"actual={self.metric.value:.2f}, "
            f"expected={self.entry.expected_value:.2f}, "
            f"deviation={self.deviation_pct:.1f}%"
        )


@dataclass
class BaselineStore:
    _entries: Dict[str, BaselineEntry] = field(default_factory=dict)

    def add(self, entry: BaselineEntry) -> None:
        self._entries[entry.name] = entry

    def get(self, name: str) -> Optional[BaselineEntry]:
        return self._entries.get(name)

    def compare(self, metric: Metric) -> Optional[BaselineResult]:
        entry = self.get(metric.name)
        if entry is None:
            return None
        dev = entry.deviation_pct(metric.value)
        return BaselineResult(
            metric=metric,
            entry=entry,
            deviation_pct=dev,
            within_tolerance=entry.is_within_tolerance(metric.value),
        )

    def compare_all(self, metrics: list[Metric]) -> list[BaselineResult]:
        results = [self.compare(m) for m in metrics]
        return [r for r in results if r is not None]


def load_baseline_store(path: Path) -> BaselineStore:
    store = BaselineStore()
    data = json.loads(path.read_text())
    for item in data:
        store.add(BaselineEntry(**item))
    return store


def save_baseline_store(store: BaselineStore, path: Path) -> None:
    data = [
        {"name": e.name, "expected_value": e.expected_value, "tolerance_pct": e.tolerance_pct}
        for e in store._entries.values()
    ]
    path.write_text(json.dumps(data, indent=2))
