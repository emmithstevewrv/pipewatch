"""Tests for alert backend configuration loading."""
from __future__ import annotations

import pytest

from pipewatch.alert_config import backends_from_config
from pipewatch.alerts import LoggingBackend, SMTPBackend


def test_empty_config_returns_no_backends():
    assert backends_from_config({}) == []


def test_logging_backend_enabled():
    cfg = {"alerts": {"logging": {"enabled": True}}}
    backends = backends_from_config(cfg)
    assert len(backends) == 1
    assert isinstance(backends[0], LoggingBackend)


def test_logging_backend_disabled():
    cfg = {"alerts": {"logging": {"enabled": False}}}
    assert backends_from_config(cfg) == []


def test_smtp_backend_enabled():
    cfg = {
        "alerts": {
            "smtp": {
                "enabled": True,
                "host": "smtp.example.com",
                "port": 587,
                "sender": "pw@example.com",
                "recipients": ["ops@example.com"],
            }
        }
    }
    backends = backends_from_config(cfg)
    assert len(backends) == 1
    b = backends[0]
    assert isinstance(b, SMTPBackend)
    assert b.host == "smtp.example.com"
    assert b.port == 587
    assert b.recipients == ["ops@example.com"]


def test_both_backends_enabled():
    cfg = {
        "alerts": {
            "logging": {"enabled": True},
            "smtp": {
                "enabled": True,
                "host": "localhost",
                "port": 25,
                "sender": "a@b.com",
                "recipients": ["c@d.com"],
            },
        }
    }
    backends = backends_from_config(cfg)
    assert len(backends) == 2
    types = {type(b) for b in backends}
    assert types == {LoggingBackend, SMTPBackend}
