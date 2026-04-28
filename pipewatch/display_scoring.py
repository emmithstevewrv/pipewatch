"""Rich display helpers for health-score results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from pipewatch.scoring import ScoredMetric

_console = Console()


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def render_scoring_table(results: list[ScoredMetric], *, console: Console | None = None) -> None:
    con = console or _console

    table = Table(
        title="Metric Health Scores",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    table.add_column("Metric", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("OK %", justify="right")
    table.add_column("Warn %", justify="right")
    table.add_column("Crit %", justify="right")
    table.add_column("Samples", justify="right")

    if not results:
        table.add_row("[dim]no data[/dim]", "-", "-", "-", "-", "-")
    else:
        for r in results:
            color = _score_color(r.score)
            table.add_row(
                r.metric_name,
                f"[{color}]{r.score:.1f}[/{color}]",
                f"{r.ok_ratio:.0%}",
                f"{r.warning_ratio:.0%}",
                f"{r.critical_ratio:.0%}",
                str(r.sample_count),
            )

    con.print(table)


def render_scoring_summary(results: list[ScoredMetric], *, console: Console | None = None) -> None:
    con = console or _console

    if not results:
        con.print("[dim]No scored metrics to summarise.[/dim]")
        return

    avg = sum(r.score for r in results) / len(results)
    worst = results[0]  # already sorted ascending
    best = results[-1]

    color = _score_color(avg)
    con.print(f"  Overall average score : [{color}]{avg:.1f}[/{color}]")
    con.print(f"  Best  metric : [green]{best.metric_name}[/green] ({best.score:.1f})")
    con.print(f"  Worst metric : [red]{worst.metric_name}[/red] ({worst.score:.1f})")
