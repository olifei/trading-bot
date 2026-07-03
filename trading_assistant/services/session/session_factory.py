"""Session-service factory.

Conversational history is persisted in a database via ADK's
``DatabaseSessionService`` so sessions survive process restarts (instead of the
prototype's in-memory sessions). The backing store is configurable:

    SESSION_DB_URL=sqlite+aiosqlite:///./trading_bot_sessions.db   # default
    SESSION_DB_URL=postgresql+asyncpg://user:pass@host/db          # production

If the persistent service cannot be constructed (e.g. missing async driver) we
fall back to the in-memory service so the app still starts.
"""
import logging
import os

from google.adk.sessions import BaseSessionService, InMemorySessionService

logger = logging.getLogger(__name__)

DEFAULT_SESSION_DB_URL = "sqlite+aiosqlite:///./trading_bot_sessions.db"


def create_session_service() -> BaseSessionService:
    """Return a persistent session service, falling back to in-memory on error."""
    db_url = os.environ.get("SESSION_DB_URL", DEFAULT_SESSION_DB_URL)
    try:
        from google.adk.sessions import DatabaseSessionService

        service = DatabaseSessionService(db_url=db_url)
        logger.info("Using DatabaseSessionService (%s)", db_url.split("://", 1)[0])
        return service
    except Exception as exc:  # pragma: no cover - depends on installed drivers
        logger.warning(
            "Falling back to InMemorySessionService (could not init '%s'): %s",
            db_url, exc,
        )
        return InMemorySessionService()


async def get_or_create_session(
    session_service: BaseSessionService,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
    state: dict | None = None,
):
    """Fetch an existing session or create it (persistent services keep history)."""
    session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=state or {"user_id": user_id},
        )
    return session
