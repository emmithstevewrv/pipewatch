"""CLI command for metric forecasting."""

from __future__ import annotations

import click

from pipewatch.history import MetricHistory
from pipewatch.forecasting import forecast_all
from pipewatch.display_forecasting import render_forecast_table, render_forecast_summary


@click.command("forecast")
@click.option(
    "--horizon",
    default=1,
    show_default=True,
    help="Number of steps ahead to forecast.",
)
@click.option(
    "--min-samples",
    default=5,
    show_default=True,
    help="Minimum samples required to produce a forecast.",
)
@click.option(
    "--summary",
    is_flag=True,
    default=False,
    help="Show only a summary instead of the full table.",
)
@click.pass_context
def forecast_cmd(ctx: click.Context, horizon: int, min_samples: int, summary: bool) -> None:
    """Forecast future metric values using linear regression."""
    history: MetricHistory = ctx.obj.get("history") if ctx.obj else None
    if history is None:
        history = MetricHistory()

    results = forecast_all(history, horizon=horizon, min_samples=min_samples)

    if not results:
        click.echo("Not enough data to produce forecasts.")
        return

    if summary:
        render_forecast_summary(results)
    else:
        render_forecast_table(results)
        render_forecast_summary(results)
