"""Rich display helpers for compressed series results."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.compression import CompressedSeries

_console = Console()


def render_compression_table(results: List[CompressedSeries]) -> None:
    """Render a summary table of compression results."""
    table = Table(
        title="Metric Compression Results",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Original", justify="right")
    table.add_column("Compressed", justify="right")
    table.add_column("Retained %", justify="right")

    for r in results:
        ratio = (
            r.compressed_count / r.original_count * 100 if r.original_count else 0.0
        )
        color = "green" if ratio >= 80 else ("yellow" if ratio >= 40 else "red")
        table.add_row(
            r.metric_name,
            str(r.original_count),
            str(r.compressed_count),
            f"[{color}]{ratio:.1f}%[/{color}]",
        )

    if not results:
        _console.print("[yellow]No compression results to display.[/yellow]")
        return

    _console.print(table)


def render_compression_summary(results: List[CompressedSeries]) -> None:
    """Print a one-line summary of overall compression."""
    if not results:
        _console.print("[yellow]No metrics compressed.[/yellow]")
        return

    total_orig = sum(r.original_count for r in results)
    total_comp = sum(r.compressed_count for r in results)
    saved = total_orig - total_comp
    pct = saved / total_orig * 100 if total_orig else 0.0

    _console.print(
        f"[bold]Compression summary:[/bold] "
        f"{len(results)} metric(s), "
        f"{total_orig} -> {total_comp} samples "
        f"([green]{pct:.1f}% reduction[/green])"
    )
