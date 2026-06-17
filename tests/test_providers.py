import pytest

from synthpanel.agent.providers import available_providers, build_provider
from synthpanel.agent.providers import test_connection as check_connection


async def test_connection_routes_per_provider():
    ok, _ = await check_connection("fake", {})
    assert ok is True

    # Each real provider routes to its own test (no creds/server -> False, no raise).
    for key in ("anthropic", "openai", "ollama"):
        ok, _ = await check_connection(key, {})
        assert ok is False

    ok, msg = await check_connection("bogus", {})
    assert ok is False
    assert "not available" in msg


def test_real_providers_are_selectable():
    keys = {p.key for p in available_providers()}
    assert {"anthropic", "openai", "ollama", "fake"} <= keys


def test_build_provider_fake_and_unknown():
    assert build_provider("fake", {}) is not None
    with pytest.raises(ValueError):
        build_provider("bogus", {})
