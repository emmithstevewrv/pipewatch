"""Eviction strategies for trimming MetricHistory based on capacity or priority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import MetricStatus


@dataclass
class EvictionPolicy:
    max_total_snapshots: int = 1000
    prefer_evict_ok: bool = True

    def __str__(self) -> str:
        pref = "ok-first" if self.prefer_evict_ok else "oldest-first"
        return f"EvictionPolicy(max={self.max_total_snapshots}, strategy={pref})"


@dataclass
class EvictionResult:
    metric_name: str
    evicted_count: int
    remaining_count: int

    def __str__(self) -> str:
        return (
            f"{self.metric_name}: evicted={self.evicted_count}, "
            f"remaining={self.remaining_count}"
        )


def _total_snapshots(history: MetricHistory) -> int:
    return sum(len(history.snapshots(name)) for name in history.metric_names())


def _evict_from_series(
    snapshots: List[MetricSnapshot],
    count: int,
    prefer_evict_ok: bool,
) -> List[MetricSnapshot]:
    """Remove *count* snapshots, preferring OK-status ones if requested."""
    if count <= 0:
        return snapshots
    if prefer_evict_ok:
        ok = [s for s in snapshots if s.status == MetricStatus.OK]
        non_ok = [s for s in snapshots if s.status != MetricStatus.OK]
        to_remove = min(count, len(ok))
        surviving_ok = ok[to_remove:]          # drop the oldest OK entries
        remainder = count - to_remove
        surviving_non_ok = non_ok[remainder:]  # fall back to oldest non-OK
        kept = sorted(surviving_ok + surviving_non_ok, key=lambda s: s.timestamp)
    else:
        kept = snapshots[count:]               # drop oldest regardless of status
    return kept


def apply_eviction(
    history: MetricHistory,
    policy: Optional[EvictionPolicy] = None,
) -> List[EvictionResult]:
    """Apply *policy* to *history* in-place and return per-metric eviction results."""
    if policy is None:
        policy = EvictionPolicy()

    results: List[EvictionResult] = []
    total = _total_snapshots(history)
    overflow = total - policy.max_total_snapshots

    if overflow <= 0:
        for name in history.metric_names():
            results.append(EvictionResult(name, 0, len(history.snapshots(name))))
        return results

    # Distribute evictions proportionally across metrics
    names = list(history.metric_names())
    counts = {n: len(history.snapshots(n)) for n in names}

    for name in names:
        share = round(overflow * counts[name] / total)
        original = history.snapshots(name)
        kept = _evict_from_series(list(original), share, policy.prefer_evict_ok)
        history._data[name] = kept  # type: ignore[attr-defined]
        results.append(EvictionResult(name, len(original) - len(kept), len(kept)))

    return results
