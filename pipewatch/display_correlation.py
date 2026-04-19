"""Rich display helpers for correlation results."""
from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich import box
from pipewatch.correlation import CorrelationResult

console = Console()


def _strength_color(coeff: float) -> str:
    abs_c = abs(coeff)
    if abs_c >= 0.7:
        return "bright_cyan"
    if abs_c >= 0.4:
        return "yellow"
    return "dim"


def render_correlation_table(results: list[CorrelationResult]) -> None:
    if not results:
        console.print("[dim]No correlation data available.[/dim]")
        return

    table = Table(
        title="Metric Correlations",
        box=box.SIMPLE_HEAD,
        show_lines=False,
    )
    table.add_column("Metric A", style="bold")
    table.add_column("Metric B", style="bold")
    table.add_column("Coefficient", justify="right")
    table.add_column("Strength")
    table.add_column("Samples", justify="right")

    for r in sorted(results, key=lambda x: -abs(x.coefficient)):
        color = _strength_color(r.coefficient)
        abs_c = abs(r.coefficient)
        strength = (
            "strong" if abs_c >= 0.7
            else "moderate" if abs_c >= 0.4
            else "weak"
        )
        direction = "+" if r.coefficient >= 0 else "-"
        table.add_row(
            r.metric_a,
            r.metric_b,
            f"[{color}]{r.coefficient:+.3f}[/{color}]",
            f"[{color}]{direction}{strength}[/{color}]",
            str(r.sample_count),
        )

    console.print(table)


def render_correlation_summary(results: list[CorrelationResult]) -> None:
    strong = [r for r in results if abs(r.coefficient) >= 0.7]
    console.print(f"[bold]Pairs analysed:[/bold] {len(results)}")
    console.print(f"[bold]Strong correlations (|r| ≥ 0.7):[/bold] {len(strong)}")
    for r in strong:
        console.print(f"  [bright_cyan]{r}[/bright_cyan]")
