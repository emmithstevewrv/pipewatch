"""Alert notification backends for pipewatch."""
from __future__ import annotations

import smtplib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import List

from pipewatch.metrics import Metric, MetricStatus

logger = logging.getLogger(__name__)


@dataclass
class AlertEvent:
    metric: Metric
    message: str

    def __str__(self) -> str:
        return (
            f"[{self.metric.status.value.upper()}] {self.metric.name}: "
            f"{self.metric.value} — {self.message}"
        )


class AlertBackend(ABC):
    @abstractmethod
    def send(self, events: List[AlertEvent]) -> None:
        """Send alert notifications for the given events."""


class LoggingBackend(AlertBackend):
    """Logs alerts using Python's logging module."""

    def send(self, events: List[AlertEvent]) -> None:
        for event in events:
            if event.metric.status == MetricStatus.CRITICAL:
                logger.critical(str(event))
            else:
                logger.warning(str(event))


@dataclass
class SMTPBackend(AlertBackend):
    """Sends alert emails via SMTP."""

    host: str
    port: int
    sender: str
    recipients: List[str]
    subject_prefix: str = "[pipewatch]"
    username: str = ""
    password: str = ""

    def send(self, events: List[AlertEvent]) -> None:
        if not events:
            return
        body = "\n".join(str(e) for e in events)
        subject = f"{self.subject_prefix} {len(events)} alert(s) detected"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        try:
            with smtplib.SMTP(self.host, self.port) as smtp:
                if self.username:
                    smtp.login(self.username, self.password)
                smtp.sendmail(self.sender, self.recipients, msg.as_string())
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to send email alert: %s", exc)


def dispatch_alerts(
    metrics: List[Metric], backends: List[AlertBackend]
) -> List[AlertEvent]:
    """Build AlertEvents for non-OK metrics and dispatch to all backends."""
    events = [
        AlertEvent(metric=m, message=f"status is {m.status.value}")
        for m in metrics
        if m.status != MetricStatus.OK
    ]
    for backend in backends:
        backend.send(events)
    return events
