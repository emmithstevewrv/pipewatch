"""Export metric history to JSON or CSV formats."""

from __future__ import annotations

import csv
import json
import io
from typing import Literal

from pipewatch.history import MetricHistory


ExportFormat = Literal["json", "csv"]


def export_history(history: MetricHistory, fmt: ExportFormat = "json") -> str:
    """Serialize all recorded metric snapshots to the requested format."""
    if fmt == "json":
        return _to_json(history)
    elif fmt == "csv":
        return _to_csv(history)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")


def _to_json(history: MetricHistory) -> str:
    rows = []
    for name in history._data:  # noqa: SLF001
        for snap in history.snapshots(name):
            rows.append({
                "metric": name,
                "value": snap.value,
                "status": snap.status.value,
                "timestamp": snap.timestamp.isoformat(),
            })
    return json.dumps(rows, indent=2)


def _to_csv(history: MetricHistory) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=["metric", "value", "status", "timestamp"]
    )
    writer.writeheader()
    for name in history._data:  # noqa: SLF001
        for snap in history.snapshots(name):
            writer.writerow({
                "metric": name,
                "value": snap.value,
                "status": snap.status.value,
                "timestamp": snap.timestamp.isoformat(),
            })
    return output.getvalue()
