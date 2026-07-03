"""A persistent, Firestore-backed long-term memory service for ADK.

Consolidated conversation facts are stored in Firestore (the project's existing
database) under::

    agent_memory/{app_name}__{user_id}/entries/{entry_id}

Retrieval uses keyword overlap ranking (the same approach as ADK's reference
``InMemoryMemoryService``), but the store is durable across restarts and shared
across sessions for a user. Firestore's client is synchronous, so blocking
calls are off-loaded with ``asyncio.to_thread`` to keep the event loop free.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List

from google.adk.memory.base_memory_service import BaseMemoryService, SearchMemoryResponse
from google.adk.memory.memory_entry import MemoryEntry
from google.genai import types

logger = logging.getLogger(__name__)

_COLLECTION = "agent_memory"
_MAX_RESULTS = 8


def _sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def _user_key(app_name: str, user_id: str) -> str:
    return f"{_sanitize(app_name)}__{_sanitize(user_id)}"


def _keywords(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[A-Za-z]+", text or "")}


def rank_entries(entries: List[Dict[str, Any]], query: str, limit: int = _MAX_RESULTS
                 ) -> List[Dict[str, Any]]:
    """Pure keyword-overlap ranking (no I/O) so it can be unit-tested.

    Returns the entries whose stored keywords intersect the query, most
    overlap first.
    """
    query_words = _keywords(query)
    if not query_words:
        return []
    scored = []
    for entry in entries:
        words = set(entry.get("keywords") or []) or _keywords(entry.get("text", ""))
        overlap = len(query_words & words)
        if overlap:
            scored.append((overlap, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


class FirestoreMemoryService(BaseMemoryService):
    """BaseMemoryService implementation backed by Firestore."""

    def __init__(self, client_factory=None):
        # Injected for tests; defaults to the shared project Firestore client.
        if client_factory is None:
            from trading_assistant.services.database.firestore_client import (
                get_firestore_client,
            )
            client_factory = get_firestore_client
        self._client_factory = client_factory

    def _entries_ref(self, app_name: str, user_id: str):
        db = self._client_factory()
        return (
            db.collection(_COLLECTION)
            .document(_user_key(app_name, user_id))
            .collection("entries")
        )

    # -- write path -------------------------------------------------------
    async def add_session_to_memory(self, session) -> None:
        entries = []
        for event in session.events or []:
            content = getattr(event, "content", None)
            if not content or not getattr(content, "parts", None):
                continue
            text = " ".join(p.text for p in content.parts if getattr(p, "text", None))
            if not text.strip():
                continue
            entries.append({
                "id": f"{_sanitize(session.id)}__{_sanitize(str(getattr(event, 'id', '')))}",
                "text": text,
                "author": getattr(event, "author", None),
                "role": getattr(content, "role", None),
                "session_id": session.id,
                "keywords": sorted(_keywords(text)),
                "timestamp": getattr(event, "timestamp", None),
            })
        if not entries:
            return
        try:
            await asyncio.to_thread(
                self._write_entries, session.app_name, session.user_id, entries
            )
            logger.info(
                "Consolidated %d memory entries for %s/%s",
                len(entries), session.app_name, session.user_id,
            )
        except Exception:  # pragma: no cover - network/permission errors
            logger.warning("Failed to write memory to Firestore", exc_info=True)

    def _write_entries(self, app_name: str, user_id: str, entries: List[Dict[str, Any]]):
        ref = self._entries_ref(app_name, user_id)
        for entry in entries:
            # Deterministic id => idempotent upsert across repeated consolidation.
            ref.document(entry["id"]).set(entry)

    # -- read path --------------------------------------------------------
    async def search_memory(self, *, app_name: str, user_id: str, query: str
                            ) -> SearchMemoryResponse:
        try:
            entries = await asyncio.to_thread(self._read_entries, app_name, user_id)
        except Exception:  # pragma: no cover - network/permission errors
            logger.warning("Failed to read memory from Firestore", exc_info=True)
            return SearchMemoryResponse()

        response = SearchMemoryResponse()
        for entry in rank_entries(entries, query):
            ts = entry.get("timestamp")
            response.memories.append(
                MemoryEntry(
                    content=types.Content(
                        role=entry.get("role") or "user",
                        parts=[types.Part(text=entry.get("text", ""))],
                    ),
                    author=entry.get("author"),
                    timestamp=str(ts) if ts is not None else None,
                )
            )
        return response

    def _read_entries(self, app_name: str, user_id: str) -> List[Dict[str, Any]]:
        return [doc.to_dict() for doc in self._entries_ref(app_name, user_id).stream()]
