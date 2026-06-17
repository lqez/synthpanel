"""End-to-end flow tests for the web app using Starlette's TestClient.

The browser run is stubbed via the 'fake' provider path; connection testing is
monkeypatched so no network/API key is needed.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def client(tmp_path):
    app = create_app(Store(tmp_path / "db.sqlite"))
    return TestClient(app)


def test_welcome_and_start_redirects_to_onboarding(client):
    assert client.get("/").status_code == 200
    # No settings yet -> Get Started routes to provider setup.
    r = client.get("/start", follow_redirects=False)
    assert r.headers["location"] == "/onboarding"


def test_onboarding_fake_provider_saves_and_advances(client):
    # Fake provider connects offline; should save and route to /projects which,
    # being empty, redirects to project creation.
    r = client.post("/onboarding", data={"provider": "fake"}, follow_redirects=False)
    assert r.headers["location"] == "/projects"

    # Now /start skips onboarding because settings exist.
    r2 = client.get("/start", follow_redirects=False)
    assert r2.headers["location"] == "/projects"

    # Empty project list jumps straight to creation (branch d).
    r3 = client.get("/projects", follow_redirects=False)
    assert r3.headers["location"] == "/projects/new"


def test_onboarding_connection_failure_rerenders(client, monkeypatch):
    async def fail(provider, config):
        return False, "bad key"

    monkeypatch.setattr("synthpanel.web.app.test_connection", fail)
    r = client.post("/onboarding", data={"provider": "anthropic", "api_key": "x"})
    assert r.status_code == 400
    assert "bad key" in r.text


def test_create_project_then_run(client, monkeypatch):
    client.post("/onboarding", data={"provider": "fake"})

    # Step 1: project basics -> redirect to persona preparation.
    r = client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "signup", "language": "en"},
        follow_redirects=False,
    )
    loc = r.headers["location"]
    assert loc.endswith("/personas")
    pid = loc.split("/")[2]

    # Step 2: save personas (none) -> project detail.
    r2 = client.post(f"/projects/{pid}/personas", data={"personas": []}, follow_redirects=False)
    assert r2.headers["location"] == f"/projects/{pid}"

    detail = client.get(f"/projects/{pid}")
    assert detail.status_code == 200
    assert "app.test" in detail.text

    # Stub execution so no browser is needed.
    async def fake_execute(project, settings, **kw):
        return {"sessions": [], "summary": {"personas": 1, "bugs": 3, "succeeded": 0}}

    monkeypatch.setattr("synthpanel.web.app.execute_run", fake_execute)
    run_resp = client.post(f"/projects/{pid}/run", follow_redirects=False)
    run_loc = run_resp.headers["location"]
    assert run_loc.startswith("/runs/")

    run_page = client.get(run_loc)
    assert run_page.status_code == 200
    assert "버그 3건" in run_page.text
