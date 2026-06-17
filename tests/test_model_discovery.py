"""Model discovery: provider list_* functions and the registry router."""

from __future__ import annotations

import anthropic
import pytest

from synthpanel.agent.anthropic_provider import list_anthropic_models
from synthpanel.agent.providers import list_models


class _Page:
    def __init__(self, ids):
        self.data = [type("M", (), {"id": i})() for i in ids]


class _Models:
    def __init__(self, ids):
        self._ids = ids

    async def list(self, **kw):
        return _Page(self._ids)


def _fake_client(ids):
    def factory(**kw):
        return type("C", (), {"models": _Models(ids)})()

    return factory


async def test_anthropic_list_parses_ids(monkeypatch):
    monkeypatch.setattr(anthropic, "AsyncAnthropic", _fake_client(["claude-opus-4-8", "claude-haiku-4-5"]))
    ok, models = await list_anthropic_models({"api_key": "k"})
    assert ok is True
    assert "claude-opus-4-8" in models


async def test_anthropic_list_requires_key():
    ok, msg = await list_anthropic_models({})
    assert ok is False
    assert "API key" in msg


async def test_registry_routes_and_fake():
    ok, models = await list_models("fake", {})
    assert ok is True and models == ["fake"]

    # Real providers route to their list_*; without creds they fail gracefully.
    for key in ("anthropic", "openai", "ollama"):
        ok, _ = await list_models(key, {})
        assert ok is False

    ok, msg = await list_models("bogus", {})
    assert ok is False and "not available" in msg
