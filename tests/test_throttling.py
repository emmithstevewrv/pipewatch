"""Tests for pipewatch.throttling."""

from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import MetricStatus
from pipewatch.throttling import AlertThrottler, ThrottlePolicy


def _now() -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def throttler() -> AlertThrottler:
    return AlertThrottler(ThrottlePolicy(cooldown_seconds=60.0, suppress_ok=True))


def test_first_alert_is_always_allowed(throttler):
    result = throttler.check("row_count", MetricStatus.WARNING, now=_now())
    assert result.allowed is True
    assert "first alert" in result.reason


def test_second_alert_within_cooldown_is_suppressed(throttler):
    t0 = _now()
    throttler.check("row_count", MetricStatus.WARNING, now=t0)
    result = throttler.check("row_count", MetricStatus.CRITICAL, now=t0 + timedelta(seconds=30))
    assert result.allowed is False
    assert result.suppressed_count == 1


def test_alert_allowed_after_cooldown_expires(throttler):
    t0 = _now()
    throttler.check("row_count", MetricStatus.WARNING, now=t0)
    result = throttler.check("row_count", MetricStatus.CRITICAL, now=t0 + timedelta(seconds=61))
    assert result.allowed is True
    assert "cooldown expired" in result.reason


def test_ok_status_suppressed_when_flag_set(throttler):
    result = throttler.check("latency", MetricStatus.OK, now=_now())
    assert result.allowed is False
    assert "suppress_ok" in result.reason


def test_ok_status_allowed_when_flag_off():
    policy = ThrottlePolicy(cooldown_seconds=60.0, suppress_ok=False)
    t = AlertThrottler(policy)
    result = t.check("latency", MetricStatus.OK, now=_now())
    assert result.allowed is True


def test_suppressed_count_increments_each_call(throttler):
    t0 = _now()
    throttler.check("errors", MetricStatus.CRITICAL, now=t0)
    for i in range(1, 4):
        result = throttler.check("errors", MetricStatus.CRITICAL, now=t0 + timedelta(seconds=i))
        assert result.suppressed_count == i


def test_reset_clears_state_for_metric(throttler):
    t0 = _now()
    throttler.check("errors", MetricStatus.CRITICAL, now=t0)
    throttler.reset("errors")
    result = throttler.check("errors", MetricStatus.CRITICAL, now=t0 + timedelta(seconds=5))
    assert result.allowed is True
    assert "first alert" in result.reason


def test_reset_all_clears_all_metrics(throttler):
    t0 = _now()
    for name in ("a", "b", "c"):
        throttler.check(name, MetricStatus.WARNING, now=t0)
    throttler.reset_all()
    for name in ("a", "b", "c"):
        result = throttler.check(name, MetricStatus.WARNING, now=t0 + timedelta(seconds=1))
        assert result.allowed is True


def test_independent_cooldowns_per_metric(throttler):
    t0 = _now()
    throttler.check("metric_a", MetricStatus.CRITICAL, now=t0)
    throttler.check("metric_b", MetricStatus.CRITICAL, now=t0)
    result_a = throttler.check("metric_a", MetricStatus.CRITICAL, now=t0 + timedelta(seconds=30))
    result_b = throttler.check("metric_b", MetricStatus.CRITICAL, now=t0 + timedelta(seconds=90))
    assert result_a.allowed is False
    assert result_b.allowed is True


def test_str_representation():
    policy = ThrottlePolicy(cooldown_seconds=120.0, suppress_ok=False)
    assert "120.0" in str(policy)
    assert "suppress_ok=False" in str(policy)
