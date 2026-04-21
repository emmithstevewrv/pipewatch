"""Rich display helpers for sampling policy status."""

from __future__ import annotations

from typing import Dict

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.sampling import MetricSampler, SamplingPolicy

_console = Console()


def render_sampling_table(sampler: MetricSampler) -> None:
    """Render a table showing sampling policy and counts for all tracked metrics."""
    table = Table(
        title="Metric Sampling Status",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Interval (s)", justify="right")
    table.add_column("Max Samples", justify="right")
    table.add_column("Jitter", justify="right")
    table.add_column("Samples Taken", justify="right", style="green")
    table.add_column("Exhausted", justify="center")

    counts = sampler.sample_counts()
    states = sampler._states  # noqa: SLF001

    if not states:
        _console.print("[dim]No metrics registered with sampler.[/dim]")
        return

    for name, state in sorted(states.items()):
        policy = state.policy
        max_s = str(policy.max_samples) if policy.max_samples is not None else "∞"
        jitter_s = f"{policy.jitter:.2f}" if policy.jitter else "—"
        exhausted = "[red]yes[/red]" if state.is_exhausted() else "[green]no[/green]"
        table.add_row(
            name,
            f"{policy.interval_seconds:.2f}",
            max_s,
            jitter_s,
            str(counts.get(name, 0)),
            exhausted,
        )

    _console.print(table)


def render_sampling_summary(sampler: MetricSampler) -> None:
    """Print a brief summary line about the sampler state."""
    counts = sampler.sample_counts()
    total = sum(counts.values())
    exhausted = sum(1 for s in sampler._states.values() if s.is_exhausted())  # noqa: SLF001
    active = len(counts) - exhausted
    _console.print(
        f"[bold]Sampling summary:[/bold] "
        f"{len(counts)} metric(s) tracked | "
        f"{total} total sample(s) | "
        f"[green]{active} active[/green] | "
        f"[red]{exhausted} exhausted[/red]"
    )
