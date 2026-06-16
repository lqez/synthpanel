"""The AI recommendation flow inside project creation (fake provider, offline)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def client(tmp_path):
    c = TestClient(create_app(Store(tmp_path / "db.sqlite")))
    c.post("/onboarding", data={"provider": "fake"})
    return c


def test_recommend_renders_panel(client):
    r = client.post(
        "/projects/recommend",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "count": "4"},
    )
    assert r.status_code == 200
    assert "추천된 페르소나" in r.text


def test_create_project_with_recommended_personas(client):
    rec = client.post(
        "/projects/recommend",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "count": "3"},
    )
    # Pull the persona tokens the recommend page rendered and submit them.
    import re

    tokens = re.findall(r'name="personas" value="([^"]+)"', rec.text)
    assert tokens
    created = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "personas": tokens[:3]},
        follow_redirects=True,
    )
    assert created.status_code == 200
    # Project detail shows the persona pills.
    assert "페르소나" in created.text
