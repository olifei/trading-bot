"""Memory-service factory.

Defaults to the persistent Firestore-backed memory service. Set
``MEMORY_BACKEND=inmemory`` to force the ephemeral service (e.g. for tests), or
``MEMORY_BACKEND=vertex_rag`` to use ADK's Vertex RAG service when configured.
"""
import logging
import os

from google.adk.memory import BaseMemoryService, InMemoryMemoryService

logger = logging.getLogger(__name__)


def create_memory_service() -> BaseMemoryService:
    backend = os.environ.get("MEMORY_BACKEND", "firestore").lower()

    if backend == "inmemory":
        return InMemoryMemoryService()

    if backend == "vertex_rag":
        try:
            from google.adk.memory import VertexAiRagMemoryService

            corpus = os.environ["RAG_CORPUS"]
            logger.info("Using VertexAiRagMemoryService")
            return VertexAiRagMemoryService(rag_corpus=corpus)
        except Exception as exc:  # pragma: no cover - optional path
            logger.warning("Vertex RAG memory unavailable (%s); using Firestore", exc)

    try:
        from trading_assistant.services.memory.firestore_memory_service import (
            FirestoreMemoryService,
        )

        logger.info("Using FirestoreMemoryService")
        return FirestoreMemoryService()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Firestore memory unavailable (%s); using in-memory", exc)
        return InMemoryMemoryService()
