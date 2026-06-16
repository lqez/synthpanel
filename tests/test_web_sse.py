"""SSE progress streaming. Uses background=False so the run completes inline and
the broker holds the full history, making the stream deterministic to assert."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from synthpanel.orchestrator import PanelProgress
from synthpanel.web.app import create_app
from synthpanel.web.store import Store


@pytest.fixture()
def client(tmp_path, monkeypatch):
    c = TestClient(create_app(Store(tmp_path / "db.sqlite"), background=False))
    c.post("/onboarding", data={"provider": "fake"})
    c.post(
        "/projects/new",
        data={"name": "App", "url": "https://app.test", "focus": "f", "personas": []},
    )

    async def fake_execute(project, settings, *, on_progress=None, **kw):
        if on_progress:
            on_progress(PanelProgress("A", "start", 0, 2))
            on_progress(PanelProgress("A", "finish", 0, 2, status="success"))
            on_progress(PanelProgress("B", "start", 1, 2))
            on_progress(PanelProgress("B", "finish", 1, 2, status="gaveup"))
        return {
            "sessions": [],
            "summary": {"personas": 2, "bugs": 0, "succeeded": 1},
        }

    monkeypatch.setattr("synthpanel.web.app.execute_run", fake_execute)
    return c


def test_run_marks_done_and_streams_progress(client):
    r = client.post("/projects/1/run", follow_redirects=False)
    run_url = r.headers["location"]
    run_id = run_url.rsplit("/", 1)[-1]

    # Inline execution already finished -> run is persisted as done.
    detail = client.get(run_url)
    assert detail.status_code == 200

    # The stream replays the buffered progress and ends with the done event.
    body = client.get(f"/runs/{run_id}/stream").text
    assert '"persona": "A"' in body
    assert '"status": "success"' in body
    assert '"status": "gaveup"' in body
    assert "event: done" in body
