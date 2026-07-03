"""ADK callbacks that capture *intent* vs *outcome* as structured events.

Wire these into an agent alongside the existing business callbacks:

    before_model_callback=[kyc_compliance_check, log_user_intent]
    before_tool_callback=[trade_params_compliance_check, log_tool_call]
    after_tool_callback=[log_tool_result]
    after_agent_callback=log_agent_outcome

Every callback is wrapped so an observability failure can never break a request.
"""
from typing import Any, Dict, Optional

from trading_assistant.observability.logging_config import get_logger, log_event
from trading_assistant.observability.redaction import redact, redact_mapping

_LOG = get_logger("trading_assistant.observability.events")

_MAX_OUTCOME_CHARS = 600


def _user_id(state: Any) -> Optional[str]:
    try:
        return state.get("user_id")
    except Exception:
        return None


def _last_user_text(llm_request: Any) -> Optional[str]:
    """Best-effort extraction of the latest user utterance from an LlmRequest."""
    try:
        for content in reversed(getattr(llm_request, "contents", []) or []):
            if getattr(content, "role", None) != "user":
                continue
            texts = [
                p.text for p in (getattr(content, "parts", []) or [])
                if getattr(p, "text", None)
            ]
            if texts:
                return " ".join(texts)
    except Exception:
        return None
    return None


def _summarize(value: Any) -> str:
    text = value if isinstance(value, str) else repr(value)
    if len(text) > _MAX_OUTCOME_CHARS:
        text = text[:_MAX_OUTCOME_CHARS] + "…"
    return text


def log_user_intent(callback_context, llm_request) -> None:
    """before_model_callback — records the user's intent for this turn."""
    try:
        log_event(
            _LOG,
            "user_intent",
            agent=getattr(callback_context, "agent_name", None),
            user_id=_user_id(callback_context.state),
            intent=redact(_last_user_text(llm_request)),
        )
    except Exception:
        _LOG.debug("failed to capture user intent", exc_info=True)
    return None


def log_tool_call(tool, args: Dict[str, Any], tool_context) -> Optional[Dict]:
    """before_tool_callback — records the intended tool action and arguments."""
    try:
        log_event(
            _LOG,
            "tool_call",
            tool=getattr(tool, "name", str(tool)),
            user_id=_user_id(tool_context.state),
            args=redact_mapping(args or {}),
        )
    except Exception:
        _LOG.debug("failed to capture tool call", exc_info=True)
    return None


def log_tool_result(tool, args: Dict[str, Any], tool_context, tool_response) -> Optional[Dict]:
    """after_tool_callback — records the actual outcome of the tool action."""
    try:
        status = None
        if isinstance(tool_response, dict):
            status = tool_response.get("status")
        log_event(
            _LOG,
            "tool_result",
            tool=getattr(tool, "name", str(tool)),
            user_id=_user_id(tool_context.state),
            status=status,
            outcome=redact(_summarize(tool_response)),
        )
    except Exception:
        _LOG.debug("failed to capture tool result", exc_info=True)
    return None


def log_agent_outcome(callback_context) -> None:
    """after_agent_callback — marks the end of an agent's turn."""
    try:
        log_event(
            _LOG,
            "agent_outcome",
            agent=getattr(callback_context, "agent_name", None),
            user_id=_user_id(callback_context.state),
        )
    except Exception:
        _LOG.debug("failed to capture agent outcome", exc_info=True)
    return None
