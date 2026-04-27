"""CLI command: `pipewatch summarize` — print a health digest."""

from __future__ import annotations

import json
from pathlib import Path

import click

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.summarization import summarize
from pipewatch.display_summarization import render_digest_table, render_digest_summary


def _demo_history() -> MetricHistory:
    """Build a small demo history for the summarize command."""
    import random
    import time

    from pipewatch.history import MetricHistory
    from pipewatch.metrics import Metric, MetricStatus, ThresholdRule, evaluate

    history = MetricHistory()
    rule = ThresholdRule(warning_below=10.0, critical_below=5.0)
    rng = random.Random(42)
    base = time.time() - 300

    for pipeline in ("ingest", "transform", "load"):
        for i in range(20):
            value = rng.uniform(2.0, 20.0)
            metric = evaluate(Metric(name=pipeline, value=value, status=MetricStatus.OK), rule)
            history.record(metric, timestamp=base + i * 15)

    return history


@click.command("summarize")
@click.option(
    "--input", "input_path",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="JSON history file produced by `pipewatch export --format json`.",
)
@click.option("--no-table", is_flag=True, default=False, help="Skip the per-metric table.")
def summarize_cmd(input_path: str | None, no_table: bool) -> None:  # pragma: no cover
    """Print a health digest summarising all tracked metrics."""
    if input_path:
        raw = json.loads(Path(input_path).read_text())
        history = MetricHistory()
        for row in raw:
            m = Metric(
                name=row["name"],
                value=row["value"],
                status=MetricStatus(row["status"]),
            )
            history.record(m, timestamp=row.get("timestamp"))
    else:
        history = _demo_history()

    digest = summarize(history)
    if not no_table:
        render_digest_table(digest)
    render_digest_summary(digest)
