"""Metric collector: applies threshold rules and stores evaluated metrics."""
from typing import Dict, List

from pipewatch.metrics import Metric, MetricStatus, ThresholdRule


class MetricCollector:
    def __init__(self, rules: List[ThresholdRule] | None = None):
        self._rules: Dict[str, ThresholdRule] = {}
        self._history: List[Metric] = []
        for rule in (rules or []):
            self.add_rule(rule)

    def add_rule(self, rule: ThresholdRule) -> None:
        self._rules[rule.metric_name] = rule

    def record(self, metric: Metric) -> Metric:
        rule = self._rules.get(metric.name)
        if rule:
            metric.status = rule.evaluate(metric)
        else:
            metric.status = MetricStatus.UNKNOWN
        self._history.append(metric)
        return metric

    def latest(self, metric_name: str) -> Metric | None:
        for m in reversed(self._history):
            if m.name == metric_name:
                return m
        return None

    def all_metrics(self) -> List[Metric]:
        return list(self._history)

    def critical_metrics(self) -> List[Metric]:
        seen = {}
        for m in reversed(self._history):
            if m.name not in seen:
                seen[m.name] = m
        return [m for m in seen.values() if m.status == MetricStatus.CRITICAL]
