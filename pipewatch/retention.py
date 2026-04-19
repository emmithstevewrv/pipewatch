"""Retention policy: prune old snapshots from MetricHistory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.history import MetricHistory


@dataclass
class RetentionPolicy:
    """Defines how long snapshots should be kept."""

    max_age_seconds: Optional[float] = None
    max_samples: Optional[int] = None

    def __str__(self) -> str:
        parts = []
        if self.max_age_seconds is not None:
            parts.append(f"max_age={self.max_age_seconds}s")
        if self.max_samples is not None:
            parts.append(f"max_samples={self.max_samples}")
        return f"RetentionPolicy({', '.join(parts) if parts else 'unlimited'})"


def apply_retention(history: MetricHistory, policy: RetentionPolicy) -> dict[str, int]:
    """Prune snapshots in *history* according to *policy*.

    Returns a dict mapping metric name -> number of snapshots removed.
    """
    removed: dict[str, int] = {}

    cutoff: Optional[datetime] = None
    if policy.max_age_seconds is not None:
        cutoff = datetime.utcnow() - timedelta(seconds=policy.max_age_seconds)

    for name in list(history._data.keys()):
        original = history._data[name]
        pruned = original

        if cutoff is not None:
            pruned = [s for s in pruned if s.timestamp >= cutoff]

        if policy.max_samples is not None and len(pruned) > policy.max_samples:
            pruned = pruned[-policy.max_samples :]

        dropped = len(original) - len(pruned)
        if dropped:
            history._data[name] = pruned
            removed[name] = dropped

    return removed
