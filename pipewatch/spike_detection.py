"""Spike detection: identify sudden value jumps between consecutive snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory


@dataclass
class SpikeEvent:
    metric_name: str
    previous_value: float
    current_value: float
    delta: float
    delta_pct: float

    def __str__(self) -> str:
        direction = "up" if self.delta > 0 else "down"
        return (
            f"{self.metric_name}: spike {direction} "
            f"{self.previous_value:.3f} -> {self.current_value:.3f} "
            f"({self.delta_pct:+.1f}%)"
        )


def detect_spike(
    history: MetricHistory,
    metric_name: str,
    threshold_pct: float = 50.0,
) -> Optional[SpikeEvent]:
    """Return a SpikeEvent if the two most recent values differ by more than
    *threshold_pct* percent, otherwise return None."""
    values = history.values(metric_name)
    if len(values) < 2:
        return None

    prev, curr = values[-2], values[-1]

    if prev == 0.0:
        # Avoid division by zero; any non-zero current is treated as a spike.
        if curr != 0.0:
            delta_pct = 100.0
        else:
            return None
    else:
        delta_pct = ((curr - prev) / abs(prev)) * 100.0

    if abs(delta_pct) >= threshold_pct:
        return SpikeEvent(
            metric_name=metric_name,
            previous_value=prev,
            current_value=curr,
            delta=curr - prev,
            delta_pct=delta_pct,
        )
    return None


def detect_all_spikes(
    history: MetricHistory,
    threshold_pct: float = 50.0,
) -> List[SpikeEvent]:
    """Run spike detection across every metric tracked in *history*."""
    results: List[SpikeEvent] = []
    for name in history.metric_names():
        event = detect_spike(history, name, threshold_pct=threshold_pct)
        if event is not None:
            results.append(event)
    return results
