"""Trading assistant package.

The root agent lives in ``trading_assistant.agent`` (ADK discovers it there).
We intentionally do NOT import it here so lightweight modules such as
``trading_assistant.schemas`` and ``trading_assistant.observability`` can be
imported (e.g. in unit tests) without pulling in the full agent / GCP stack.
"""
