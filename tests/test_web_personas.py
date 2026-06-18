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


def test_recommended_persona_persisted_on_save(ctx):
    client, store = ctx
    before = len(store.list_personas())

    # Step 1: create the project, then recommend + save personas in step 2.
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "language": "en"},
        follow_redirects=False,
    )
    pid = r.headers["location"].split("/")[2]
    rec = client.post(f"/projects/{pid}/personas/recommend", data={"count": "2"})
    tokens = re.findall(r'data-token="([^"]+)"', rec.text)
    client.post(f"/projects/{pid}/personas", data={"personas": tokens[:2]}, follow_redirects=True)

    # New (recommended) personas were saved into the library.
    assert len(store.list_personas()) >= before
    assert any(p["source"] == "custom" for p in store.list_personas())
