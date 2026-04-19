"""High-level 'watch' command: collect metrics on a schedule and display/alert."""

import logging
from typing import List

from pipewatch.collector import MetricCollector
from pipewatch.scheduler import MetricScheduler
from pipewatch.alerts import AlertDispatcher
from pipewatch.display import render_metrics_table, render_alert_summary
from pipewatch.history import MetricHistory

logger = logging.getLogger(__name__)


class WatchSession:
    """Ties together a collector, history, scheduler, and alert dispatcher."""

    def __init__(
        self,
        collector: MetricCollector,
        dispatcher: AlertDispatcher,
        interval: float = 30.0,
        history_limit: int = 100,
    ):
        self.collector = collector
        self.dispatcher = dispatcher
        self.history = MetricHistory(max_snapshots=history_limit)
        self._scheduler = MetricScheduler(interval=interval, task=self._tick)

    def start(self) -> None:
        logger.info("WatchSession starting.")
        self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.stop()
        logger.info("WatchSession stopped.")

    def _tick(self) -> None:
        metrics = self.collector.latest()
        if not metrics:
            logger.debug("No metrics available yet.")
            return

        for metric in metrics:
            self.history.record(metric)

        alerts = self.dispatcher.evaluate(metrics)

        print(render_metrics_table(metrics))
        if alerts:
            print(render_alert_summary(alerts))

    @property
    def running(self) -> bool:
        return self._scheduler.running
