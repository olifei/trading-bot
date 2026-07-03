"""Unit tests for redaction and structured logging (no GCP / network required)."""
import json
import logging

from trading_assistant.observability.logging_config import JsonFormatter, log_event
from trading_assistant.observability.redaction import redact, redact_mapping


def test_redact_masks_pii_but_keeps_numbers():
    assert redact("email me a.b@example.com") == "email me [REDACTED]"
    assert redact("api_key=sk-secret-123").endswith("[REDACTED]")
    # trading numbers must survive redaction
    assert "60000.50" in redact("bought BTC at 60000.50 USDT")


def test_redact_mapping_masks_sensitive_keys():
    out = redact_mapping({"email": "x@y.com", "token": "abc", "price": "42"})
    assert out == {"email": "[REDACTED]", "token": "[REDACTED]", "price": "42"}


def test_json_formatter_emits_structured_fields():
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1,
        msg="tool_call", args=(), exc_info=None,
    )
    record.event = "tool_call"
    record.structured = {"tool": "get_price", "args": {"symbol": "BTC"}}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["event"] == "tool_call"
    assert payload["severity"] == "INFO"
    assert payload["tool"] == "get_price"
    assert payload["args"] == {"symbol": "BTC"}


def test_log_event_redacts(caplog):
    logger = logging.getLogger("test.events")
    logger.setLevel(logging.INFO)
    with caplog.at_level(logging.INFO, logger="test.events"):
        log_event(logger, "user_intent", intent="reach me at a.b@example.com")
    rec = next(r for r in caplog.records if getattr(r, "event", None) == "user_intent")
    payload = json.loads(JsonFormatter().format(rec))
    assert payload["intent"] == "reach me at [REDACTED]"
