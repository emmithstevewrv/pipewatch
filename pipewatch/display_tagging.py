"""Rich display helpers for tagged snapshot data."""

from __future__ import annotations

from typing import Dict, List

from rich.console import Console
from rich.table import Table

from pipewatch.tagging import TaggedSnapshot

_console = Console()


def render_tagged_table(tagged: List[TaggedSnapshot], title: str = "Tagged Snapshots") -> None:
    """Render a Rich table of TaggedSnapshots."""
    table = Table(title=title, show_lines=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Tags")

    for t in tagged:
        snap = t.snapshot
        status = snap.status.value if snap.status else "unknown"
        color = {"ok": "green", "warning": "yellow", "critical": "red"}.get(status, "white")
        tag_str = " ".join(f"{k}={v}" for k, v in t.tags.items()) or "—"
        table.add_row(
            snap.name,
            f"{snap.value:.4g}",
            f"[{color}]{status}[/{color}]",
            tag_str,
        )

    _console.print(table)


def render_tag_group_summary(
    groups: Dict[str, List[TaggedSnapshot]],
    tag_key: str,
) -> None:
    """Render a summary table grouped by a tag key."""
    table = Table(title=f"Grouped by tag: {tag_key}", show_lines=False)
    table.add_column("Tag Value", style="magenta")
    table.add_column("Count", justify="right")
    table.add_column("Metrics")

    for tag_val, items in sorted(groups.items()):
        names = ", ".join(sorted({t.snapshot.name for t in items}))
        table.add_row(tag_val or "(none)", str(len(items)), names)

    _console.print(table)
