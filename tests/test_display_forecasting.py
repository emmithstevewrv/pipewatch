"""Smoke tests for display_forecasting rendering functions."""

from __future__ import annotations

import io
from rich.console import Console

import pipewatch.display_forecasting as df_mod
from pipewatch.forecasting import ForecastResult


def _make_result(name: str, slope: float) -> ForecastResult:
    return ForecastResult(
        metric_name=name,
        horizon=1,
        predicted_value=42.0 + slope,
        slope=slope,
        intercept=1.0,
        sample_count=10,
    )


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    original = df_mod.console
    df_mod.console = Console(file=buf, highlight=False)
    try:
        fn(*args, **kwargs)
    finally:
        df_mod.console = original
    return buf.getvalue()


def test_render_table_contains_metric_names():
    results = [_make_result("cpu", 0.5), _make_result("mem", -0.2)]
    output = _capture(df_mod.render_forecast_table, results)
    assert "cpu" in output
    assert "mem" in output


def test_render_table_shows_horizon():
    results = [_make_result("latency", 0.0)]
    output = _capture(df_mod.render_forecast_table, results)
    assert "+1" in output


def test_render_summary_empty():
    output = _capture(df_mod.render_forecast_summary, [])
    assert "No forecast data" in output


def test_render_summary_counts():
    results = [
        _make_result("a", 1.0),
        _make_result("b", -1.0),
        _make_result("c", 0.0),
    ]
    output = _capture(df_mod.render_forecast_summary, results)
    assert "1 rising" in output
    assert "1 falling" in output
    assert "1 flat" in output
