"""Structured JSON logging with automatic trace correlation and PII redaction.

Every log record is emitted as a single-line JSON object so it can be ingested
directly by Cloud Logging / any log pipeline. When an OpenTelemetry span is
active the ``trace_id`` / ``span_id`` are attached so logs and traces line up.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from trading_assistant.observability.redaction import redact, redact_mapping

try:  # optional; logs still work without OpenTelemetry installed
    from opentelemetry import trace as _otel_trace
except Exception:  # pragma: no cover - defensive
    _otel_trace = None

_RESERVED = frozenset(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Render a ``LogRecord`` as a redacted JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }

        trace_ctx = _current_trace_context()
        if trace_ctx:
            payload.update(trace_ctx)

        event = getattr(record, "event", None)
        if event:
            payload["event"] = event
        structured = getattr(record, "structured", None)
        if isinstance(structured, dict):
            payload.update(redact_mapping(structured))

        # capture any ad-hoc `extra=` fields as well
        for key, value in record.__dict__.items():
            if key in _RESERVED or key in ("event", "structured"):
                continue
            if key.startswith("_"):
                continue
            payload.setdefault(key, redact_mapping(value))

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


def _current_trace_context() -> Optional[Dict[str, str]]:
    if _otel_trace is None:
        return None
    try:
        span = _otel_trace.get_current_span()
        ctx = span.get_span_context()
        if ctx is None or ctx.trace_id == 0:
            return None
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    except Exception:  # pragma: no cover - defensive
        return None


def configure_logging(level: Optional[str] = None) -> None:
    """Install the JSON formatter on the root logger. Idempotent."""
    level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO,
              message: Optional[str] = None, **fields: Any) -> None:
    """Emit a structured event. ``fields`` are redacted and nested under the log line.

    Example::

        log_event(logger, "tool_call", tool="execute_spot_order", args={...})
    """
    logger.log(
        level,
        message or event,
        extra={"event": event, "structured": fields},
    )
