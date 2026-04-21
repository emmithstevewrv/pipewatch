"""Periodic metric collection scheduler for pipewatch."""

import time
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SchedulerStop(Exception):
    pass


class MetricScheduler:
    """Runs a collection function on a fixed interval in a background thread."""

    def __init__(self, interval: float, task: Callable[[], None]):
        self.interval = interval
        self.task = task
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._error_count: int = 0

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Scheduler is already running.")
        self._stop_event.clear()
        self._error_count = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Scheduler started with interval=%.1fs", self.interval)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the scheduler to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("Scheduler stopped.")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.task()
            except Exception as exc:  # pylint: disable=broad-except
                self._error_count += 1
                logger.error(
                    "Scheduler task raised an exception (total errors: %d): %s",
                    self._error_count,
                    exc,
                )
            self._stop_event.wait(self.interval)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def error_count(self) -> int:
        """Return the number of exceptions raised by the task since last start."""
        return self._error_count
