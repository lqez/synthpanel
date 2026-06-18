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


def test_recommended_personas_selected_from_library_and_saved(ctx):
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
    # Recommended personas render first (in #lib-rec-data), before the library list.
    tokens = re.findall(r'data-token="([^"]+)"', rec.text)
    client.post(f"/projects/{pid}/personas", data={"personas": tokens[:2]}, follow_redirects=True)

    # Recommendations are drawn from the existing library, so saving snapshots
    # them into the project without creating duplicate library rows.
    saved = store.get_project(int(pid))["personas"]
    assert len(saved) == 2
    assert len(store.list_personas()) == before


def test_recommend_clears_previous_selection(ctx):
    client, store = ctx
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "language": "en"},
        follow_redirects=False,
    )
    pid = r.headers["location"].split("/")[2]

    # Save two personas to the project so it has a prior selection.
    rec = client.post(f"/projects/{pid}/personas/recommend", data={"count": "2"})
    tokens = re.findall(r'data-token="([^"]+)"', rec.text)
    client.post(f"/projects/{pid}/personas", data={"personas": tokens[:2]}, follow_redirects=True)

    # Re-opening the page shows the saved personas pre-selected...
    page = client.get(f"/projects/{pid}/personas")
    assert 'data-checked="true"' in page.text

    # ...but recommending again starts fresh: nothing from the library stays
    # pre-selected (only the new recommendations, rendered in #lib-rec-data).
    again = client.post(f"/projects/{pid}/personas/recommend", data={"count": "2"})
    assert 'data-checked="true"' not in again.text


def test_recommend_persists_focus_to_project(ctx):
    client, store = ctx
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "language": "en"},
        follow_redirects=False,
    )
    pid = r.headers["location"].split("/")[2]
    assert store.get_project(int(pid))["focus"] == ""  # focus starts empty

    client.post(f"/projects/{pid}/personas/recommend", data={"count": "2", "focus": "접근성 검토"})
    # The focus entered when recommending is reflected back into the project.
    assert store.get_project(int(pid))["focus"] == "접근성 검토"
