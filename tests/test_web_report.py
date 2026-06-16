"""Run a project (stubbed execution) and check the report views render."""

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


_RESULT = {
    "sessions": [
        {
            "persona_name": "A",
            "status": "gaveup",
            "steps": [],
            "bugs": [{"title": "Checkout fails", "severity": "critical"}],
            "ux_feedback": "stuck at payment",
        },
        {
            "persona_name": "B",
            "status": "gaveup",
            "steps": [],
            "bugs": [{"title": "checkout fails", "severity": "major"}],
            "ux_feedback": "",
        },
    ],
    "summary": {"personas": 2, "bugs": 2, "succeeded": 0},
}


@pytest.fixture()
def run_url(client, monkeypatch):
    client.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "checkout", "personas": []},
    )

    async def fake_execute(project, settings, **kw):
        return _RESULT

    monkeypatch.setattr("synthpanel.web.app.execute_run", fake_execute)
    r = client.post("/projects/1/run", follow_redirects=False)
    return r.headers["location"]


def test_run_detail_shows_aggregated_issues(client, run_url):
    page = client.get(run_url)
    assert page.status_code == 200
    assert "공통 이슈" in page.text
    assert "Checkout fails" in page.text
    assert "2×" in page.text  # the two checkout bugs clustered


def test_markdown_and_html_reports(client, run_url):
    run_id = run_url.rsplit("/", 1)[-1]
    md = client.get(f"/runs/{run_id}/report.md")
    assert md.status_code == 200
    assert "# Usability report" in md.text

    html = client.get(f"/runs/{run_id}/report.html")
    assert html.status_code == 200
    assert html.text.startswith("<!doctype html>")
    assert "Checkout fails" in html.text
