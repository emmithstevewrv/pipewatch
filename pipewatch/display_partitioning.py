"""Rich display helpers for partitioning results."""

from __future__ import annotations

from typing import Dict, List

from rich.console import Console
from rich.table import Table

from pipewatch.partitioning import Partition

_console = Console()


def render_partition_table(
    partitions_by_metric: Dict[str, List[Partition]],
    *,
    console: Console | None = None,
) -> None:
    """Render a table showing partition counts and means per metric."""
    con = console or _console
    if not partitions_by_metric:
        con.print("[yellow]No partition data available.[/yellow]")
        return

    table = Table(title="Metric Partitions", show_lines=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Partition", style="bold")
    table.add_column("Range", justify="center")
    table.add_column("Count", justify="right")
    table.add_column("Mean", justify="right")

    for metric_name, partitions in sorted(partitions_by_metric.items()):
        for i, part in enumerate(partitions):
            mean_str = f"{part.mean:.4f}" if part.mean is not None else "-"
            table.add_row(
                metric_name if i == 0 else "",
                part.label,
                f"[{part.low}, {part.high})",
                str(part.count),
                mean_str,
            )

    con.print(table)


def render_partition_summary(
    partitions_by_metric: Dict[str, List[Partition]],
    *,
    console: Console | None = None,
) -> None:
    """Print a one-line summary of total metrics and partition buckets."""
    con = console or _console
    total_metrics = len(partitions_by_metric)
    total_buckets = sum(
        len(parts) for parts in partitions_by_metric.values()
    )
    total_snaps = sum(
        p.count
        for parts in partitions_by_metric.values()
        for p in parts
    )
    con.print(
        f"[bold]Partitioning:[/bold] {total_metrics} metric(s), "
        f"{total_buckets} bucket(s), {total_snaps} classified snapshot(s)."
    )
