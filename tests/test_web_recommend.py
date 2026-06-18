"""AI recommendation in the per-project persona-preparation step (offline)."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def client(tmp_path):
    c = TestClient(create_app(Store(tmp_path / "db.sqlite")))
    c.post("/onboarding", data={"provider": "fake"})
    return c


def _new_project(client) -> str:
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "language": "en"},
        follow_redirects=False,
    )
    return r.headers["location"].split("/")[2]  # project id


def test_recommend_renders_panel(client):
    pid = _new_project(client)
    r = client.post(f"/projects/{pid}/personas/recommend", data={"count": "4"})
    assert r.status_code == 200
    assert re.search(r'id="lib-rec-data".*data-token', r.text, re.DOTALL)


def test_save_recommended_personas(client):
    pid = _new_project(client)
    rec = client.post(f"/projects/{pid}/personas/recommend", data={"count": "3"})
    tokens = re.findall(r'data-token="([^"]+)"', rec.text)
    assert tokens

    saved = client.post(
        f"/projects/{pid}/personas",
        data={"personas": tokens[:3]},
        follow_redirects=True,
    )
    assert saved.status_code == 200
    assert "페르소나" in saved.text  # project detail lists them
