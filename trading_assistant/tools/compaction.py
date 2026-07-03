"""History compaction to manage context bloat.

When a conversation grows past a threshold, older turns are folded into a
compact textual summary that is appended to the system instruction, and only the
most recent turns are kept in ``llm_request.contents``. This is deterministic
(no extra LLM call), keeps token usage bounded, and avoids role-ordering issues
by summarising into the system prompt rather than the message list.

Tunable via env:
    HISTORY_MAX_CONTENTS   trigger compaction above this many contents (default 12)
    HISTORY_KEEP_RECENT    number of recent contents to preserve verbatim (default 6)
"""
import os
from typing import Any, List, Optional

from trading_assistant.observability.logging_config import get_logger, log_event

logger = get_logger("trading_assistant.memory.compaction")

_MAX_SNIPPET = 160


def _content_text(content: Any) -> str:
    parts = getattr(content, "parts", None) or []
    return " ".join(p.text for p in parts if getattr(p, "text", None)).strip()


def summarize_contents(contents: List[Any]) -> str:
    """Build a compact, deterministic summary of older conversation turns."""
    lines = []
    for content in contents:
        text = _content_text(content)
        if not text:
            continue
        if len(text) > _MAX_SNIPPET:
            text = text[:_MAX_SNIPPET] + "…"
        role = getattr(content, "role", "user") or "user"
        lines.append(f"- {role}: {text}")
    header = f"[Earlier conversation summary — {len(lines)} messages compacted]"
    return header + "\n" + "\n".join(lines)


def compact_history(callback_context, llm_request) -> Optional[Any]:
    """before_model_callback that compacts long histories in place."""
    try:
        max_contents = int(os.environ.get("HISTORY_MAX_CONTENTS", "12"))
        keep_recent = int(os.environ.get("HISTORY_KEEP_RECENT", "6"))
        contents = list(getattr(llm_request, "contents", None) or [])
        if len(contents) <= max_contents:
            return None

        older, recent = contents[:-keep_recent], contents[-keep_recent:]
        summary = summarize_contents(older)

        config = getattr(llm_request, "config", None)
        if config is not None:
            base = getattr(config, "system_instruction", None) or ""
            config.system_instruction = f"{base}\n\n{summary}"
        llm_request.contents = recent

        log_event(
            logger, "history_compacted",
            agent=getattr(callback_context, "agent_name", None),
            compacted=len(older), kept=len(recent),
        )
    except Exception:
        logger.debug("history compaction skipped", exc_info=True)
    return None
