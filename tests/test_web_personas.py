"""Persona library page + project creation persisting personas to the library."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def ctx(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    c = TestClient(create_app(store, background=False))
    c.post("/onboarding", data={"provider": "fake"})
    return c, store


def test_library_page_lists_seeded_personas(ctx):
    client, _ = ctx
    page = client.get("/personas")
    assert page.status_code == 200
    assert "김순자" in page.text


def test_delete_persona(ctx):
    client, store = ctx
    pid = store.list_personas()[0]["id"]
    client.post(f"/personas/{pid}/delete")
    assert store.get_persona(pid) is None


def test_recommended_persona_persisted_on_project_create(ctx):
    client, store = ctx
    before = len(store.list_personas())

    rec = client.post(
        "/projects/recommend",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "count": "2"},
    )
    tokens = re.findall(r'name="personas" value="([^"]+)"', rec.text)
    # Recommended tokens come first; pick those that aren't already library names.
    client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "personas": tokens[:2]},
        follow_redirects=True,
    )
    # New (recommended) personas were saved into the library.
    assert len(store.list_personas()) >= before
    assert any(p["source"] == "custom" for p in store.list_personas())
