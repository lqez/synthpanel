"""Welcome screen shows saved settings; /start validates before entering."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(Store(tmp_path / "db.sqlite")))


def test_welcome_first_time_shows_get_started(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "Get Started" in page.text


def test_welcome_shows_saved_settings_and_start_button(client):
    client.post("/onboarding", data={"provider": "fake"})
    page = client.get("/")
    assert "바로 시작하기" in page.text
    assert "fake" in page.text  # saved provider shown


def test_start_validates_and_enters_when_valid(client):
    client.post("/onboarding", data={"provider": "fake"})  # fake always connects
    r = client.get("/start", follow_redirects=False)
    assert r.headers["location"] == "/projects"


def test_start_redirects_to_onboarding_with_error_when_invalid(client, monkeypatch):
    client.post("/onboarding", data={"provider": "fake"})

    async def fail(provider, config):
        return False, "stale key"

    monkeypatch.setattr("synthpanel.web.app.test_connection", fail)
    r = client.get("/start", follow_redirects=False)
    loc = r.headers["location"]
    assert loc.startswith("/onboarding?")
    # The error is surfaced on the onboarding page.
    assert "유효하지" in client.get(loc).text


def test_start_without_settings_goes_to_onboarding(client):
    r = client.get("/start", follow_redirects=False)
    assert r.headers["location"] == "/onboarding"
