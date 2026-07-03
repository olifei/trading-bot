"""Observability layer: structured logging, tracing, PII redaction and
intent/outcome capture for the trading assistant.

Typical bootstrap (done once at process start):

    from trading_assistant.observability import setup_observability
    setup_observability(service_name="trading-bot-server")
"""
from trading_assistant.observability.logging_config import (
    configure_logging,
    get_logger,
    log_event,
)
from trading_assistant.observability.tracing import get_tracer, init_tracing
from trading_assistant.observability.redaction import redact, redact_mapping


def setup_observability(service_name: str = "trading-assistant") -> None:
    """Initialise structured logging + tracing. Safe to call more than once."""
    configure_logging()
    init_tracing(service_name=service_name)


__all__ = [
    "setup_observability",
    "configure_logging",
    "get_logger",
    "log_event",
    "init_tracing",
    "get_tracer",
    "redact",
    "redact_mapping",
]
