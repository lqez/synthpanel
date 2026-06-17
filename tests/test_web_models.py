"""The onboarding 'load models' flow renders a model dropdown."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(Store(tmp_path / "db.sqlite")))


def test_load_models_renders_dropdown(client, monkeypatch):
    async def fake_list(provider, config):
        assert provider == "anthropic"
        assert config["api_key"] == "k"
        return True, ["claude-opus-4-8", "claude-haiku-4-5"]

    monkeypatch.setattr("synthpanel.web.app.list_models", fake_list)
    r = client.post("/onboarding/models", data={"provider": "anthropic", "api_key": "k"})
    assert r.status_code == 200
    assert '<select name="model">' in r.text
    assert "claude-opus-4-8" in r.text


def test_load_models_failure_shows_error(client, monkeypatch):
    async def fail(provider, config):
        return False, "bad key"

    monkeypatch.setattr("synthpanel.web.app.list_models", fail)
    r = client.post("/onboarding/models", data={"provider": "anthropic", "api_key": "x"})
    assert r.status_code == 200
    assert "모델 목록을 못 불러왔어요" in r.text
    # Falls back to a text input so the user isn't blocked.
    assert 'name="model"' in r.text
