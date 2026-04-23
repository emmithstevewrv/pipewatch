"""CLI command for partitioning metric history into value-range buckets."""

from __future__ import annotations

import click

from pipewatch.display_partitioning import (
    render_partition_summary,
    render_partition_table,
)
from pipewatch.history import MetricHistory
from pipewatch.partitioning import partition_all


@click.command("partition")
@click.option(
    "--bucket",
    "buckets",
    multiple=True,
    metavar="LABEL:LOW:HIGH",
    required=True,
    help="Define a bucket as LABEL:LOW:HIGH (may be repeated).",
)
@click.pass_context
def partition_cmd(ctx: click.Context, buckets: tuple[str, ...]) -> None:
    """Partition recorded metrics into user-defined value-range buckets.

    Example:\n
        pipewatch partition --bucket low:0:50 --bucket high:50:100
    """
    history: MetricHistory = ctx.obj["history"]

    bounds = []
    for raw in buckets:
        parts = raw.split(":")
        if len(parts) != 3:  # noqa: PLR2004
            raise click.BadParameter(
                f"Expected LABEL:LOW:HIGH, got {raw!r}", param_hint="--bucket"
            )
        label, low_s, high_s = parts
        try:
            bounds.append((label, float(low_s), float(high_s)))
        except ValueError:
            raise click.BadParameter(
                f"LOW and HIGH must be numbers, got {low_s!r} / {high_s!r}",
                param_hint="--bucket",
            )

    result = partition_all(history, bounds)
    render_partition_table(result)
    render_partition_summary(result)
