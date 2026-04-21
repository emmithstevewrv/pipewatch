"""Rich display helpers for metric segmentation results."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.segmentation import Segment

_console = Console()


def render_segment_table(
    metric_name: str,
    segments: List[Segment],
    console: Console | None = None,
) -> None:
    """Render a table of segments for a single metric."""
    out = console or _console

    table = Table(
        title=f"Segments — {metric_name}",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Window", style="cyan", no_wrap=True)
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Samples", justify="right")
    table.add_column("Mean", justify="right", style="green")

    for seg in segments:
        mean_str = f"{seg.mean:.4f}" if seg.mean is not None else "—"
        table.add_row(
            seg.label,
            seg.start.strftime("%H:%M:%S"),
            seg.end.strftime("%H:%M:%S"),
            str(seg.sample_count),
            mean_str,
        )

    out.print(table)


def render_segment_summary(
    all_segments: dict[str, List[Segment]],
    console: Console | None = None,
) -> None:
    """Render a summary table across all metrics."""
    out = console or _console

    if not all_segments:
        out.print("[yellow]No segmentation data available.[/yellow]")
        return

    table = Table(title="Segmentation Summary", box=box.SIMPLE_HEAVY)
    table.add_column("Metric", style="cyan")
    table.add_column("Windows", justify="right")
    table.add_column("Total Samples", justify="right")
    table.add_column("Earliest Mean", justify="right")
    table.add_column("Latest Mean", justify="right")

    for name, segs in all_segments.items():
        total = sum(s.sample_count for s in segs)
        earliest = segs[0].mean if segs else None
        latest = segs[-1].mean if segs else None
        e_str = f"{earliest:.4f}" if earliest is not None else "—"
        l_str = f"{latest:.4f}" if latest is not None else "—"
        table.add_row(name, str(len(segs)), str(total), e_str, l_str)

    out.print(table)
