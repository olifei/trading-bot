"""OpenTelemetry tracing setup.

Google ADK automatically emits spans (invocation / agent_run / call_llm /
execute_tool) whenever a global ``TracerProvider`` is registered, so calling
``init_tracing()`` at start-up is enough to get end-to-end distributed traces.

Exporter selection (by environment):
  * ``OTEL_EXPORTER_OTLP_ENDPOINT`` set -> OTLP exporter (Cloud Trace collector, etc.)
  * ``OTEL_CONSOLE_EXPORT=true``        -> pretty console exporter (local dev)
  * otherwise                           -> provider with no exporter (spans still
                                           enrich logs via trace correlation)
"""
import logging
import os
from typing import Optional

_LOG = logging.getLogger(__name__)
_initialized = False


def init_tracing(service_name: str = "trading-assistant") -> None:
    """Register a global TracerProvider. Safe to call multiple times."""
    global _initialized
    if _initialized:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )
    except Exception as exc:  # pragma: no cover - optional dependency
        _LOG.warning("OpenTelemetry SDK unavailable, tracing disabled: %s", exc)
        return

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": "trading-assistant",
            "deployment.environment": os.environ.get("APP_ENV", "development"),
        }
    )
    provider = TracerProvider(resource=resource)

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
            _LOG.info("Tracing exporting via OTLP to %s", endpoint)
        except Exception as exc:  # pragma: no cover - defensive
            _LOG.warning("OTLP exporter unavailable (%s); falling back to console", exc)
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif os.environ.get("OTEL_CONSOLE_EXPORT", "").lower() in ("1", "true", "yes"):
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _initialized = True


def get_tracer(name: str = "trading-assistant"):
    """Return an OTel tracer, or ``None`` if OpenTelemetry is not installed."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except Exception:  # pragma: no cover - optional dependency
        return None
