"""Project creation is split: step 1 basics, step 2 persona preparation."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def ctx(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    c = TestClient(create_app(store))
    c.post("/onboarding", data={"provider": "fake"})
    return c, store


def test_step1_has_no_persona_picker(ctx):
    client, _ = ctx
    page = client.get("/projects/new")
    assert "1 / 2" in page.text
    # No persona checkboxes on the basics step.
    assert 'name="personas"' not in page.text


def test_step1_redirects_to_persona_prep(ctx):
    client, store = ctx
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "f", "language": "en"},
        follow_redirects=False,
    )
    loc = r.headers["location"]
    assert loc.endswith("/personas")
    # Project exists with no personas yet.
    pid = int(loc.split("/")[2])
    assert store.get_project(pid)["personas"] == []


def test_persona_prep_lists_library_and_saves(ctx):
    client, store = ctx
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "f", "language": "en"},
        follow_redirects=False,
    )
    pid = int(r.headers["location"].split("/")[2])

    prep = client.get(f"/projects/{pid}/personas")
    assert prep.status_code == 200
    assert "김순자" in prep.text
    tokens = re.findall(r'name="personas" value="([^"]+)"', prep.text)

    client.post(f"/projects/{pid}/personas", data={"personas": tokens[:1]})
    assert len(store.get_project(pid)["personas"]) == 1


def test_personas_are_editable(ctx):
    client, store = ctx
    pid = int(
        client.post(
            "/projects/new",
            data={"name": "App", "url": "u", "focus": "f", "language": "en"},
            follow_redirects=False,
        ).headers["location"].split("/")[2]
    )
    tokens = re.findall(
        r'name="personas" value="([^"]+)"', client.get(f"/projects/{pid}/personas").text
    )
    client.post(f"/projects/{pid}/personas", data={"personas": tokens[:2]})
    assert len(store.get_project(pid)["personas"]) == 2
    # Re-edit down to one.
    client.post(f"/projects/{pid}/personas", data={"personas": tokens[:1]})
    assert len(store.get_project(pid)["personas"]) == 1
