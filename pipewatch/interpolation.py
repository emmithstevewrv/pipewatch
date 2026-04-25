"""Gap-filling interpolation for metric history series."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot
from pipewatch.metrics import Metric, MetricStatus


@dataclass
class InterpolatedSeries:
    """A metric series with gaps filled by linear interpolation."""

    metric_name: str
    timestamps: List[datetime]
    values: List[float]
    interpolated_flags: List[bool]  # True where value was synthesised

    def __str__(self) -> str:  # pragma: no cover
        filled = sum(self.interpolated_flags)
        return (
            f"InterpolatedSeries({self.metric_name!r}, "
            f"points={len(self.values)}, filled={filled})"
        )


def _linear_fill(
    t0: float, v0: float, t1: float, v1: float, t: float
) -> float:
    """Return linearly interpolated value at time *t* between two anchors."""
    if t1 == t0:
        return v0
    return v0 + (v1 - v0) * (t - t0) / (t1 - t0)


def interpolate_metric(
    history: MetricHistory,
    metric_name: str,
    interval_seconds: float = 60.0,
) -> Optional[InterpolatedSeries]:
    """Fill gaps in *metric_name*'s history at a regular *interval_seconds* grid.

    Returns ``None`` when fewer than two snapshots exist.
    """
    snaps: List[MetricSnapshot] = history.snapshots(metric_name)
    if len(snaps) < 2:
        return None

    snaps = sorted(snaps, key=lambda s: s.timestamp)
    anchors = [(s.timestamp.timestamp(), s.metric.value) for s in snaps]

    t_start = anchors[0][0]
    t_end = anchors[-1][0]

    timestamps: List[datetime] = []
    values: List[float] = []
    flags: List[bool] = []

    t = t_start
    anchor_idx = 0
    while t <= t_end + 1e-9:
        # Advance anchor window
        while anchor_idx + 1 < len(anchors) - 1 and anchors[anchor_idx + 1][0] <= t:
            anchor_idx += 1

        t0, v0 = anchors[anchor_idx]
        t1, v1 = anchors[anchor_idx + 1]

        # Check if *t* coincides with an anchor
        is_original = any(abs(a[0] - t) < 1e-6 for a in anchors)
        val = _linear_fill(t0, v0, t1, v1, t)

        timestamps.append(datetime.fromtimestamp(t))
        values.append(round(val, 6))
        flags.append(not is_original)

        t += interval_seconds

    return InterpolatedSeries(
        metric_name=metric_name,
        timestamps=timestamps,
        values=values,
        interpolated_flags=flags,
    )


def interpolate_all(
    history: MetricHistory,
    interval_seconds: float = 60.0,
) -> List[InterpolatedSeries]:
    """Run interpolation for every metric tracked in *history*."""
    results = []
    for name in history.metric_names():
        result = interpolate_metric(history, name, interval_seconds)
        if result is not None:
            results.append(result)
    return results
