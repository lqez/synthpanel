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


def test_vote_endpoints(ctx):
    client, store = ctx
    pid = store.list_personas()[0]["id"]

    client.post(f"/personas/{pid}/vote", data={"dir": "up"})
    client.post(f"/personas/{pid}/vote", data={"dir": "up"})
    client.post(f"/personas/{pid}/vote", data={"dir": "down"})
    assert store.get_persona(pid)["votes"] == 1


def test_favorite_endpoint_and_rendering(ctx):
    client, store = ctx
    pid = store.list_personas()[0]["id"]

    client.post(f"/personas/{pid}/favorite")
    assert store.get_persona(pid)["favorite"] is True
    # The starred state renders on the library page.
    assert "★" in client.get("/personas").text
