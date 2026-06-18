"""Welcome screen tests the saved settings on load and shows status inline."""

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


def test_welcome_shows_connected_status_and_start(client):
    client.post("/onboarding", data={"provider": "fake"})  # fake always connects
    page = client.get("/")
    assert "fake" in page.text          # saved provider shown
    assert "연결됨" in page.text          # status checked on load
    assert 'href="/projects"' in page.text  # can start


def test_welcome_shows_failure_status(client, monkeypatch):
    client.post("/onboarding", data={"provider": "fake"})

    async def fail(provider, config):
        return False, "stale key"

    monkeypatch.setattr("synthpanel.web.app.test_connection", fail)
    page = client.get("/")
    assert "연결 실패" in page.text
    assert "stale key" in page.text
    # No "시작하기" start button on failure; only the settings link.
    assert "시작하기" not in page.text
    assert 'href="/onboarding"' in page.text


def test_start_enters_when_settings_exist(client):
    client.post("/onboarding", data={"provider": "fake"})
    r = client.get("/start", follow_redirects=False)
    assert r.headers["location"] == "/projects"


def test_start_without_settings_goes_to_onboarding(client):
    r = client.get("/start", follow_redirects=False)
    assert r.headers["location"] == "/onboarding"
