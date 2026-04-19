"""CLI entry point for pipewatch metric commands."""
import json
from pathlib import Path

import typer

from pipewatch.collector import MetricCollector
from pipewatch.display import render_alert_summary, render_metrics_table
from pipewatch.metrics import Metric, ThresholdRule

app = typer.Typer(name="pipewatch", help="Monitor ETL pipeline health metrics.")


def _load_rules(rules_path: Path) -> list[ThresholdRule]:
    data = json.loads(rules_path.read_text())
    return [
        ThresholdRule(
            metric_name=r["metric_name"],
            warning_above=r.get("warning_above"),
            critical_above=r.get("critical_above"),
            warning_below=r.get("warning_below"),
            critical_below=r.get("critical_below"),
        )
        for r in data
    ]


@app.command()
def check(
    metrics_file: Path = typer.Argument(..., help="JSON file with metric readings."),
    rules_file: Path = typer.Option(None, "--rules", "-r", help="JSON file with threshold rules."),
    alerts_only: bool = typer.Option(False, "--alerts-only", "-a"),
):
    """Evaluate pipeline metrics against threshold rules."""
    raw = json.loads(metrics_file.read_text())
    rules = _load_rules(rules_file) if rules_file else []
    collector = MetricCollector(rules=rules)

    for entry in raw:
        collector.record(Metric(
            name=entry["name"],
            value=float(entry["value"]),
            unit=entry.get("unit", ""),
            tags=entry.get("tags", {}),
        ))

    if alerts_only:
        render_alert_summary(collector.critical_metrics())
    else:
        render_metrics_table(collector.all_metrics())
        render_alert_summary(collector.critical_metrics())

    if collector.critical_metrics():
        raise typer.Exit(code=2)


def main():
    app()
