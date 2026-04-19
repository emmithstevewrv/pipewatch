"""Load alert backend configuration from a TOML/dict config."""
from __future__ import annotations

from typing import Any, Dict, List

from pipewatch.alerts import AlertBackend, LoggingBackend, SMTPBackend


def backends_from_config(config: Dict[str, Any]) -> List[AlertBackend]:
    """Instantiate alert backends from a configuration dictionary.

    Expected structure::

        [alerts.logging]
        enabled = true

        [alerts.smtp]
        enabled = true
        host = "smtp.example.com"
        port = 587
        sender = "pipewatch@example.com"
        recipients = ["ops@example.com"]
        username = "user"
        password = "secret"
    """
    alerts_cfg: Dict[str, Any] = config.get("alerts", {})
    backends: List[AlertBackend] = []

    log_cfg = alerts_cfg.get("logging", {})
    if log_cfg.get("enabled", False):
        backends.append(LoggingBackend())

    smtp_cfg = alerts_cfg.get("smtp", {})
    if smtp_cfg.get("enabled", False):
        backends.append(
            SMTPBackend(
                host=smtp_cfg["host"],
                port=int(smtp_cfg["port"]),
                sender=smtp_cfg["sender"],
                recipients=smtp_cfg["recipients"],
                subject_prefix=smtp_cfg.get("subject_prefix", "[pipewatch]"),
                username=smtp_cfg.get("username", ""),
                password=smtp_cfg.get("password", ""),
            )
        )

    return backends
