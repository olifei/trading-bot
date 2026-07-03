"""Tests for the Firestore memory service (ranking + add/search roundtrip).

A small in-memory fake stands in for the Firestore client so no network or
credentials are needed.
"""
from types import SimpleNamespace

import pytest

from trading_assistant.services.memory.firestore_memory_service import (
    FirestoreMemoryService,
    rank_entries,
)


def test_rank_entries_orders_by_overlap():
    entries = [
        {"text": "buy BTC now", "keywords": ["buy", "btc", "now"]},
        {"text": "sell ETH later", "keywords": ["sell", "eth", "later"]},
        {"text": "BTC price and buy", "keywords": ["btc", "price", "and", "buy"]},
    ]
    ranked = rank_entries(entries, "buy btc")
    assert ranked[0]["text"] in ("buy BTC now", "BTC price and buy")
    assert all("eth" not in e.get("keywords", []) for e in ranked)


def test_rank_entries_empty_query_returns_nothing():
    assert rank_entries([{"text": "x", "keywords": ["x"]}], "") == []


# --- fake Firestore client -------------------------------------------------
class _Snap:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class _Col:
    def __init__(self, store):
        self._store = store

    def document(self, doc_id):
        return _Doc(self._store, doc_id)

    def stream(self):
        return [_Snap(v) for k, v in self._store.items() if not isinstance(k, tuple)]


class _Doc:
    def __init__(self, store, doc_id):
        self._store = store
        self._id = doc_id

    def set(self, data):
        self._store[self._id] = data

    def collection(self, name):
        sub = self._store.setdefault((self._id, name), {})
        return _Col(sub)


class _DB:
    def __init__(self):
        self._top = {}

    def collection(self, name):
        return _Col(self._top.setdefault(name, {}))


def _session(events):
    return SimpleNamespace(app_name="trading_bot", user_id="user1", id="s1", events=events)


def _event(eid, role, text, author="user"):
    return SimpleNamespace(
        id=eid,
        author=author,
        timestamp=1700000000.0,
        content=SimpleNamespace(role=role, parts=[SimpleNamespace(text=text)]),
    )


@pytest.mark.asyncio
async def test_add_and_search_roundtrip():
    db = _DB()
    svc = FirestoreMemoryService(client_factory=lambda: db)

    session = _session([
        _event("e1", "user", "I want to buy BTC"),
        _event("e2", "model", "Placed a BTC order", author="spot_agent"),
        _event("e3", "user", "show my ETH balance"),
    ])
    await svc.add_session_to_memory(session)

    resp = await svc.search_memory(app_name="trading_bot", user_id="user1", query="BTC order")
    texts = [m.content.parts[0].text for m in resp.memories]
    assert any("BTC" in t for t in texts)
    assert all(m.content.role in ("user", "model") for m in resp.memories)


@pytest.mark.asyncio
async def test_search_no_match_returns_empty():
    db = _DB()
    svc = FirestoreMemoryService(client_factory=lambda: db)
    await svc.add_session_to_memory(_session([_event("e1", "user", "buy BTC")]))
    resp = await svc.search_memory(app_name="trading_bot", user_id="user1", query="weather forecast")
    assert resp.memories == []
