import pytest

from synthpanel.agent.providers import build_provider
from synthpanel.agent.providers import test_connection as check_connection


async def test_connection_routes_per_provider():
    ok, _ = await check_connection("fake", {})
    assert ok is True

    ok, _ = await check_connection("anthropic", {})  # no key -> False, no raise
    assert ok is False

    ok, msg = await check_connection("openai", {})
    assert ok is False
    assert "not available" in msg


def test_build_provider_fake_and_unknown():
    assert build_provider("fake", {}) is not None
    with pytest.raises(ValueError):
        build_provider("openai", {})
