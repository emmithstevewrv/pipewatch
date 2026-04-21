"""Tests for pipewatch.sampling."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.sampling import MetricSampler, SamplingPolicy, SamplerState


def make_metric(name: str = "cpu", value: float = 0.5) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, unit="%")


@pytest.fixture()
def history() -> MetricHistory:
    return MetricHistory()


@pytest.fixture()
def sampler(history: MetricHistory) -> MetricSampler:
    return MetricSampler(history, default_policy=SamplingPolicy(interval_seconds=1.0))


# --- SamplingPolicy ---

def test_policy_str_includes_interval():
    p = SamplingPolicy(interval_seconds=5.0)
    assert "5.0s" in str(p)


def test_policy_str_includes_max_samples():
    p = SamplingPolicy(interval_seconds=1.0, max_samples=10)
    assert "max=10" in str(p)


# --- SamplerState ---

def test_state_is_due_initially():
    state = SamplerState(policy=SamplingPolicy(interval_seconds=1.0))
    assert state.is_due(now=time.monotonic()) is True


def test_state_not_due_immediately_after_sample():
    state = SamplerState(policy=SamplingPolicy(interval_seconds=60.0))
    now = time.monotonic()
    state.mark_sampled(now)
    assert state.is_due(now=now) is False


def test_state_exhausted_when_max_reached():
    state = SamplerState(policy=SamplingPolicy(interval_seconds=0.0, max_samples=2))
    state.mark_sampled()
    state.mark_sampled()
    assert state.is_exhausted() is True


def test_state_not_exhausted_without_max():
    state = SamplerState(policy=SamplingPolicy(interval_seconds=0.0))
    for _ in range(100):
        state.mark_sampled()
    assert state.is_exhausted() is False


# --- MetricSampler ---

def test_should_sample_returns_true_initially(sampler: MetricSampler):
    assert sampler.should_sample("cpu", now=time.monotonic()) is True


def test_should_not_sample_after_mark(sampler: MetricSampler):
    now = time.monotonic()
    sampler.should_sample("cpu", now=now)
    sampler._state_for("cpu").mark_sampled(now)
    assert sampler.should_sample("cpu", now=now) is False


def test_record_if_due_adds_to_history(sampler: MetricSampler, history: MetricHistory):
    metric = make_metric("cpu", 0.9)
    recorded = sampler.record_if_due(metric, now=time.monotonic())
    assert recorded is True
    assert history.latest("cpu") is not None


def test_record_if_due_skips_when_not_due(sampler: MetricSampler, history: MetricHistory):
    now = time.monotonic()
    metric = make_metric("cpu", 0.9)
    sampler.record_if_due(metric, now=now)
    recorded_again = sampler.record_if_due(metric, now=now)
    assert recorded_again is False
    assert len(history.snapshots("cpu")) == 1


def test_set_policy_overrides_default(sampler: MetricSampler):
    sampler.set_policy("mem", SamplingPolicy(interval_seconds=0.0, max_samples=3))
    now = time.monotonic()
    for _ in range(3):
        sampler.record_if_due(make_metric("mem"), now=now)
    assert sampler.should_sample("mem", now=now) is False


def test_sample_counts_tracks_per_metric(sampler: MetricSampler):
    sampler.set_policy("cpu", SamplingPolicy(interval_seconds=0.0))
    sampler.set_policy("mem", SamplingPolicy(interval_seconds=0.0))
    for _ in range(3):
        sampler._state_for("cpu").mark_sampled()
    sampler._state_for("mem").mark_sampled()
    counts = sampler.sample_counts()
    assert counts["cpu"] == 3
    assert counts["mem"] == 1
