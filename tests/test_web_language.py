"""Web flow: global default language, per-project override, and run wiring."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    store = Store(tmp_path / "db.sqlite")
    c = TestClient(create_app(store, background=False))
    c.post("/onboarding", data={"provider": "fake"})
    return c, store


def test_preferences_sets_global_default(ctx):
    client, store = ctx
    client.post("/preferences", data={"language": "ko"})
    assert store.get_language() == "ko"
    # The project form pre-selects the global default.
    assert "selected" in client.get("/projects/new").text


def test_run_uses_project_language(ctx, monkeypatch):
    client, store = ctx
    client.post("/preferences", data={"language": "ko"})
    # Create a project overriding the language to Japanese.
    client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "f", "language": "ja", "personas": []},
    )

    captured = {}

    async def fake_execute(project, settings, *, language="en", **kw):
        captured["language"] = language
        return {"sessions": [], "summary": {"personas": 1, "bugs": 0, "succeeded": 0}}

    monkeypatch.setattr("synthpanel.web.app.execute_run", fake_execute)
    client.post("/projects/1/run")
    # Project-level language wins over the global default.
    assert captured["language"] == "ja"
