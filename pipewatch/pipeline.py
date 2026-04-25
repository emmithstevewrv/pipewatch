"""Pipeline-level aggregation: group metrics by pipeline tag and compute health scores."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus
from pipewatch.query import status_counts


@dataclass
class PipelineHealth:
    pipeline: str
    total: int
    ok: int
    warning: int
    critical: int
    score: float  # 0.0 (all critical) – 1.0 (all ok)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"Pipeline({self.pipeline!r} score={self.score:.2f} "
            f"ok={self.ok} warn={self.warning} crit={self.critical})"
        )


def _score(ok: int, warning: int, critical: int) -> float:
    """Weighted health score: ok=1, warning=0.5, critical=0."""
    total = ok + warning + critical
    if total == 0:
        return 1.0
    return (ok * 1.0 + warning * 0.5) / total


def pipeline_health(
    history: MetricHistory,
    tags: Dict[str, str],
    pipeline_tag: str = "pipeline",
) -> List[PipelineHealth]:
    """Compute per-pipeline health from the latest snapshot of each metric.

    Args:
        history: populated MetricHistory.
        tags: mapping of metric_name -> pipeline label.
        pipeline_tag: key used to group (informational; callers supply the mapping).

    Returns:
        Sorted list of PipelineHealth, best score first.
    """
    buckets: Dict[str, Dict[str, int]] = {}

    for metric_name, pipeline_label in tags.items():
        latest = history.latest(metric_name)
        if latest is None:
            continue
        bucket = buckets.setdefault(pipeline_label, {"ok": 0, "warning": 0, "critical": 0})
        status = latest.status
        if status == MetricStatus.OK:
            bucket["ok"] += 1
        elif status == MetricStatus.WARNING:
            bucket["warning"] += 1
        elif status == MetricStatus.CRITICAL:
            bucket["critical"] += 1

    results: List[PipelineHealth] = []
    for label, counts in buckets.items():
        ok, warn, crit = counts["ok"], counts["warning"], counts["critical"]
        results.append(
            PipelineHealth(
                pipeline=label,
                total=ok + warn + crit,
                ok=ok,
                warning=warn,
                critical=crit,
                score=_score(ok, warn, crit),
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return results
