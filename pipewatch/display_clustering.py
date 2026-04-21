"""Rich display helpers for metric clustering results."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.clustering import Cluster

_console = Console()


def render_cluster_table(clusters: List[Cluster], *, console: Console | None = None) -> None:
    """Render a table showing each cluster and its member metrics."""
    con = console or _console

    if not clusters:
        con.print("[yellow]No clusters to display.[/yellow]")
        return

    table = Table(
        title="Metric Clusters",
        box=box.SIMPLE_HEAVY,
        show_lines=True,
    )
    table.add_column("Cluster", style="bold cyan", no_wrap=True)
    table.add_column("Centroid", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Metrics")

    for cluster in clusters:
        table.add_row(
            cluster.label,
            f"{cluster.centroid:.3f}",
            f"{cluster.min_value:.3f}",
            f"{cluster.max_value:.3f}",
            ", ".join(cluster.metric_names),
        )

    con.print(table)


def render_cluster_summary(clusters: List[Cluster], *, console: Console | None = None) -> None:
    """Print a one-line summary of clustering results."""
    con = console or _console

    if not clusters:
        con.print("[yellow]Clustering produced no results.[/yellow]")
        return

    total_metrics = sum(len(c.metric_names) for c in clusters)
    con.print(
        f"[bold]Clustering summary:[/bold] "
        f"{len(clusters)} cluster(s) across {total_metrics} metric(s)."
    )
