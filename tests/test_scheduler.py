"""Tests for pipewatch.scheduler."""

import time
import threading
import pytest
from pipewatch.scheduler import MetricScheduler


def test_task_is_called_multiple_times():
    counter = {"n": 0}
    lock = threading.Lock()

    def task():
        with lock:
            counter["n"] += 1

    scheduler = MetricScheduler(interval=0.05, task=task)
    scheduler.start()
    time.sleep(0.22)
    scheduler.stop()

    assert counter["n"] >= 3


def test_scheduler_stops_cleanly():
    def task():
        pass

    scheduler = MetricScheduler(interval=0.05, task=task)
    scheduler.start()
    assert scheduler.running
    scheduler.stop()
    assert not scheduler.running


def test_double_start_raises():
    scheduler = MetricScheduler(interval=1.0, task=lambda: None)
    scheduler.start()
    try:
        with pytest.raises(RuntimeError, match="already running"):
            scheduler.start()
    finally:
        scheduler.stop()


def test_task_exception_does_not_crash_scheduler():
    calls = {"n": 0}

    def bad_task():
        calls["n"] += 1
        raise ValueError("boom")

    scheduler = MetricScheduler(interval=0.05, task=bad_task)
    scheduler.start()
    time.sleep(0.18)
    scheduler.stop()

    assert calls["n"] >= 2
    assert not scheduler.running


def test_not_running_before_start():
    scheduler = MetricScheduler(interval=1.0, task=lambda: None)
    assert not scheduler.running
