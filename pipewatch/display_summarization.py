"""Rich display helpers for HealthDigest / MetricDigest."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.metrics import MetricStatus
from pipewatch.summarization import HealthDigest

_console = Console()

_STATUS_COLOR: dict[MetricStatus, str] = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
}


def render_digest_table(digest: HealthDigest, *, console: Console | None = None) -> None:
    """Render a table with one row per metric in the digest."""
    out = console or _console

    if not digest.metrics:
        out.print("[dim]No metrics to display.[/dim]")
        return

    table = Table(
        title="Pipeline Health Digest",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold")
    table.add_column("Samples", justify="right")
    table.add_column("Latest Value", justify="right")
    table.add_column("Latest Status", justify="center")
    table.add_column("Dominant", justify="center")
    table.add_column("OK %", justify="right")
    table.add_column("Warn %", justify="right")
    table.add_column("Crit %", justify="right")

    for m in digest.metrics:
        ls_color = _STATUS_COLOR.get(m.latest_status, "white")
        dom_color = _STATUS_COLOR.get(m.dominant_status, "white")
        val_str = f"{m.latest_value:.4g}" if m.latest_value is not None else "—"
        table.add_row(
            m.name,
            str(m.sample_count),
            val_str,
            f"[{ls_color}]{m.latest_status.value}[/{ls_color}]",
            f"[{dom_color}]{m.dominant_status.value}[/{dom_color}]",
            f"{m.ok_pct:.1f}",
            f"{m.warning_pct:.1f}",
            f"{m.critical_pct:.1f}",
        )

    out.print(table)


def render_digest_summary(digest: HealthDigest, *, console: Console | None = None) -> None:
    """Print a one-line summary of the digest."""
    out = console or _console
    ok = len(digest.ok_metrics)
    warn = len(digest.warning_metrics)
    crit = len(digest.critical_metrics)
    out.print(
        f"[bold]Digest:[/bold] {digest.total_metrics} metrics, "
        f"{digest.total_samples} samples — "
        f"[green]{ok} ok[/green]  "
        f"[yellow]{warn} warning[/yellow]  "
        f"[red]{crit} critical[/red]"
    )
