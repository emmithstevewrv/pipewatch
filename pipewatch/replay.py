"""Replay historical metric snapshots at a controlled speed for testing and demos."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class ReplayConfig:
    """Configuration for a replay session."""

    speed_factor: float = 1.0  # 2.0 = twice as fast, 0.5 = half speed
    max_snapshots: Optional[int] = None  # cap total snapshots replayed
    metric_names: Optional[List[str]] = None  # None means all metrics

    def __str__(self) -> str:
        names = ", ".join(self.metric_names) if self.metric_names else "all"
        cap = str(self.max_snapshots) if self.max_snapshots else "unlimited"
        return f"ReplayConfig(speed={self.speed_factor}x, metrics={names}, cap={cap})"


@dataclass
class ReplayResult:
    """Summary produced after a replay session completes."""

    replayed: int = 0
    skipped: int = 0
    metrics_seen: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"ReplayResult(replayed={self.replayed}, skipped={self.skipped}, "
            f"metrics={len(self.metrics_seen)})"
        )


def _iter_snapshots(
    history: MetricHistory,
    metric_names: Optional[List[str]],
) -> Iterator[MetricSnapshot]:
    """Yield snapshots in chronological order across all requested metrics."""
    names = metric_names if metric_names is not None else history.metric_names()
    all_snapshots: List[MetricSnapshot] = []
    for name in names:
        all_snapshots.extend(history.snapshots(name))
    all_snapshots.sort(key=lambda s: s.timestamp)
    yield from all_snapshots


def replay_history(
    history: MetricHistory,
    on_snapshot: Callable[[MetricSnapshot], None],
    config: Optional[ReplayConfig] = None,
    *,
    _sleep: Callable[[float], None] = time.sleep,
) -> ReplayResult:
    """Replay *history* calling *on_snapshot* for each snapshot.

    Timing between consecutive snapshots is preserved and scaled by
    ``config.speed_factor``.  Pass ``_sleep`` to override for testing.
    """
    cfg = config or ReplayConfig()
    result = ReplayResult()
    prev_ts: Optional[float] = None

    for snapshot in _iter_snapshots(history, cfg.metric_names):
        if cfg.max_snapshots is not None and result.replayed >= cfg.max_snapshots:
            result.skipped += 1
            continue

        if prev_ts is not None:
            gap = (snapshot.timestamp - prev_ts) / cfg.speed_factor
            if gap > 0:
                _sleep(gap)

        on_snapshot(snapshot)
        result.replayed += 1
        prev_ts = snapshot.timestamp

        if snapshot.metric.name not in result.metrics_seen:
            result.metrics_seen.append(snapshot.metric.name)

    return result
