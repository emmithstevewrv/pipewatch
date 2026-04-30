"""Rich display helpers for labeled snapshot data."""

from __future__ import annotations

from typing import Dict, List

from rich.console import Console
from rich.table import Table

from pipewatch.labeling import LabeledSnapshot

_console = Console()


def render_labeled_table(
    labeled: List[LabeledSnapshot],
    label_keys: List[str],
    *,
    console: Console | None = None,
) -> None:
    """Render a table of labeled snapshots, with one column per label key."""
    con = console or _console
    if not labeled:
        con.print("[dim]No labeled snapshots to display.[/dim]")
        return

    table = Table(title="Labeled Snapshots", show_lines=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right")
    table.add_column("Status", justify="center")
    for key in label_keys:
        table.add_column(key, style="magenta")

    for ls in labeled:
        snap = ls.snapshot
        status = snap.metric.status.value if snap.metric.status else "unknown"
        row = [
            snap.metric.name,
            f"{snap.metric.value:.4g}",
            status,
        ]
        for key in label_keys:
            row.append(ls.labels.get(key, "-"))
        table.add_row(*row)

    con.print(table)


def render_label_group_summary(
    groups: Dict[str, List[LabeledSnapshot]],
    label_key: str,
    *,
    console: Console | None = None,
) -> None:
    """Render a summary table showing snapshot counts per label value."""
    con = console or _console
    if not groups:
        con.print("[dim]No label groups to display.[/dim]")
        return

    table = Table(title=f"Groups by '{label_key}'", show_lines=False)
    table.add_column(label_key, style="magenta", no_wrap=True)
    table.add_column("Snapshots", justify="right")

    for value, items in sorted(groups.items()):
        label = value if value else "[dim](none)[/dim]"
        table.add_row(label, str(len(items)))

    con.print(table)
