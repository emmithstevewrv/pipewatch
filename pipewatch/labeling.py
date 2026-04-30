"""Metric labeling: attach key-value labels to snapshots for grouping and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class LabeledSnapshot:
    """A snapshot decorated with a set of key-value labels."""

    snapshot: MetricSnapshot
    labels: Dict[str, str] = field(default_factory=dict)

    def has_label(self, key: str, value: Optional[str] = None) -> bool:
        """Return True if the label key exists (and optionally matches value)."""
        if key not in self.labels:
            return False
        return value is None or self.labels[key] == value

    def __str__(self) -> str:
        label_str = ", ".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
        return f"LabeledSnapshot({self.snapshot.metric.name} [{label_str}])"


def label_snapshots(
    history: MetricHistory,
    label_map: Dict[str, Dict[str, str]],
) -> List[LabeledSnapshot]:
    """Attach labels to every snapshot based on metric name.

    Args:
        history:   Populated MetricHistory instance.
        label_map: Mapping of metric_name -> {label_key: label_value}.
                   Metrics not present in the map receive empty labels.

    Returns:
        List of LabeledSnapshot objects for all recorded snapshots.
    """
    result: List[LabeledSnapshot] = []
    for name in history.metric_names():
        labels = label_map.get(name, {})
        for snap in history.snapshots(name):
            result.append(LabeledSnapshot(snapshot=snap, labels=dict(labels)))
    return result


def filter_by_label(
    labeled: List[LabeledSnapshot],
    key: str,
    value: Optional[str] = None,
) -> List[LabeledSnapshot]:
    """Return only those LabeledSnapshots that carry the given label."""
    return [ls for ls in labeled if ls.has_label(key, value)]


def group_by_label(
    labeled: List[LabeledSnapshot],
    key: str,
) -> Dict[str, List[LabeledSnapshot]]:
    """Partition labeled snapshots by the value of a specific label key.

    Snapshots that lack the key are placed under the empty-string bucket.
    """
    groups: Dict[str, List[LabeledSnapshot]] = {}
    for ls in labeled:
        bucket = ls.labels.get(key, "")
        groups.setdefault(bucket, []).append(ls)
    return groups
