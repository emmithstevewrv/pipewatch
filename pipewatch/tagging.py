"""Metric tagging: attach arbitrary key-value tags to snapshots and filter/group by them."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory, MetricSnapshot


@dataclass
class TaggedSnapshot:
    """A MetricSnapshot decorated with a tag dictionary."""

    snapshot: MetricSnapshot
    tags: Dict[str, str] = field(default_factory=dict)

    def has_tag(self, key: str, value: Optional[str] = None) -> bool:
        """Return True if *key* is present (and optionally matches *value*)."""
        if key not in self.tags:
            return False
        return value is None or self.tags[key] == value

    def __str__(self) -> str:  # pragma: no cover
        tag_str = ", ".join(f"{k}={v}" for k, v in self.tags.items())
        return f"{self.snapshot.name}[{tag_str}] = {self.snapshot.value}"


def tag_snapshots(
    history: MetricHistory,
    tags: Dict[str, str],
    metric_name: Optional[str] = None,
) -> List[TaggedSnapshot]:
    """Wrap every snapshot in *history* (or only those for *metric_name*) with *tags*."""
    names = [metric_name] if metric_name else history.metric_names()
    result: List[TaggedSnapshot] = []
    for name in names:
        for snap in history.snapshots(name):
            result.append(TaggedSnapshot(snapshot=snap, tags=dict(tags)))
    return result


def filter_by_tag(
    tagged: List[TaggedSnapshot],
    key: str,
    value: Optional[str] = None,
) -> List[TaggedSnapshot]:
    """Return only those TaggedSnapshots whose tags match *key* (and optional *value*)."""
    return [t for t in tagged if t.has_tag(key, value)]


def group_by_tag(
    tagged: List[TaggedSnapshot],
    key: str,
) -> Dict[str, List[TaggedSnapshot]]:
    """Group TaggedSnapshots by the value of *key*; snapshots missing the key go to ''."""
    groups: Dict[str, List[TaggedSnapshot]] = {}
    for t in tagged:
        bucket = t.tags.get(key, "")
        groups.setdefault(bucket, []).append(t)
    return groups
