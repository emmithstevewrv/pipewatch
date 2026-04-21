"""Metric sampling strategies for controlling data collection frequency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional
import time

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class SamplingPolicy:
    """Controls how frequently a metric is sampled."""

    interval_seconds: float = 1.0
    max_samples: Optional[int] = None
    jitter: float = 0.0  # fractional jitter applied to interval

    def __str__(self) -> str:
        parts = [f"interval={self.interval_seconds}s"]
        if self.max_samples is not None:
            parts.append(f"max={self.max_samples}")
        if self.jitter:
            parts.append(f"jitter={self.jitter}")
        return f"SamplingPolicy({', '.join(parts)})"


@dataclass
class SamplerState:
    """Tracks per-metric sampling state."""

    policy: SamplingPolicy
    last_sampled: float = field(default_factory=lambda: 0.0)
    sample_count: int = 0

    def is_due(self, now: Optional[float] = None) -> bool:
        """Return True if enough time has elapsed for the next sample."""
        import random

        now = now if now is not None else time.monotonic()
        interval = self.policy.interval_seconds
        if self.policy.jitter:
            interval += random.uniform(0, self.policy.jitter * interval)
        return (now - self.last_sampled) >= interval

    def is_exhausted(self) -> bool:
        """Return True if max_samples has been reached."""
        if self.policy.max_samples is None:
            return False
        return self.sample_count >= self.policy.max_samples

    def mark_sampled(self, now: Optional[float] = None) -> None:
        self.last_sampled = now if now is not None else time.monotonic()
        self.sample_count += 1


class MetricSampler:
    """Manages sampling policies for multiple metrics."""

    def __init__(self, history: MetricHistory, default_policy: Optional[SamplingPolicy] = None) -> None:
        self._history = history
        self._default_policy = default_policy or SamplingPolicy()
        self._states: Dict[str, SamplerState] = {}

    def set_policy(self, metric_name: str, policy: SamplingPolicy) -> None:
        """Assign a sampling policy to a named metric."""
        self._states[metric_name] = SamplerState(policy=policy)

    def _state_for(self, metric_name: str) -> SamplerState:
        if metric_name not in self._states:
            self._states[metric_name] = SamplerState(policy=self._default_policy)
        return self._states[metric_name]

    def should_sample(self, metric_name: str, now: Optional[float] = None) -> bool:
        """Return True if the metric should be sampled right now."""
        state = self._state_for(metric_name)
        if state.is_exhausted():
            return False
        return state.is_due(now)

    def record_if_due(self, metric: Metric, now: Optional[float] = None) -> bool:
        """Record the metric into history if its sampling policy allows it."""
        name = metric.name
        if not self.should_sample(name, now):
            return False
        self._history.record(metric)
        self._state_for(name).mark_sampled(now)
        return True

    def sample_counts(self) -> Dict[str, int]:
        """Return a dict of metric_name -> number of samples recorded."""
        return {name: state.sample_count for name, state in self._states.items()}
