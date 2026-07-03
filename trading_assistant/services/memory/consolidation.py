"""Asynchronous memory consolidation.

After a turn completes we push the session into long-term memory in the
background so the user's response is never blocked by the write. Failures are
swallowed (best-effort) and logged.
"""
import asyncio
import logging

from google.adk.memory import BaseMemoryService
from google.adk.sessions import BaseSessionService

from trading_assistant.observability.logging_config import get_logger, log_event

logger = get_logger("trading_assistant.memory.consolidation")


async def _consolidate(
    memory_service: BaseMemoryService,
    session_service: BaseSessionService,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
) -> None:
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        if session is None:
            return
        await memory_service.add_session_to_memory(session)
        log_event(
            logger, "memory_consolidated",
            user_id=user_id, session_id=session_id,
            events=len(session.events or []),
        )
    except Exception:
        logger.warning("memory consolidation failed", exc_info=True)


def schedule_consolidation(
    memory_service: BaseMemoryService,
    session_service: BaseSessionService,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
) -> "asyncio.Task | None":
    """Fire-and-forget consolidation task. Returns the task (or None on failure)."""
    try:
        return asyncio.create_task(
            _consolidate(
                memory_service, session_service,
                app_name=app_name, user_id=user_id, session_id=session_id,
            )
        )
    except RuntimeError:  # no running loop
        logger.debug("no event loop; skipping async consolidation")
        return None
