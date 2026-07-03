"""Tests for history compaction (context-bloat management)."""
from types import SimpleNamespace

from trading_assistant.tools.compaction import compact_history, summarize_contents


def _content(role, text):
    return SimpleNamespace(role=role, parts=[SimpleNamespace(text=text)])


def _req(contents, system=""):
    return SimpleNamespace(
        contents=list(contents),
        config=SimpleNamespace(system_instruction=system),
    )


def test_summarize_contents_includes_all_messages():
    contents = [_content("user", "buy BTC"), _content("model", "done")]
    summary = summarize_contents(contents)
    assert "2 messages compacted" in summary
    assert "user: buy BTC" in summary and "model: done" in summary


def test_no_compaction_below_threshold(monkeypatch):
    monkeypatch.setenv("HISTORY_MAX_CONTENTS", "12")
    req = _req([_content("user", f"m{i}") for i in range(5)])
    before = list(req.contents)
    assert compact_history(SimpleNamespace(agent_name="root"), req) is None
    assert req.contents == before  # untouched


def test_compaction_trims_and_appends_summary(monkeypatch):
    monkeypatch.setenv("HISTORY_MAX_CONTENTS", "6")
    monkeypatch.setenv("HISTORY_KEEP_RECENT", "3")
    contents = [_content("user", f"msg{i}") for i in range(10)]
    req = _req(contents, system="BASE")
    compact_history(SimpleNamespace(agent_name="root"), req)
    # only the most recent 3 remain in the message list
    assert len(req.contents) == 3
    assert req.contents[-1].parts[0].text == "msg9"
    # older 7 were folded into the system instruction
    assert "BASE" in req.config.system_instruction
    assert "7 messages compacted" in req.config.system_instruction
