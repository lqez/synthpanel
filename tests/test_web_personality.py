import pytest
from fastapi.testclient import TestClient

from synthpanel.agent.llm import Turn
from synthpanel.agent.prompts import render_user_turn
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation
from synthpanel.web.app import create_app
from synthpanel.web.store import Store


def test_prompt_includes_personality():
    persona = Persona(
        name="Alex",
        personality="Tends to double-check everything; dryly sarcastic.",
        intent=Intent(goal="g"),
    )
    turn = Turn(persona=persona, observation=Observation(url="u"), history=[], step_idx=0)
    text = render_user_turn(turn)
    assert "PERSONALITY:" in text
    assert "double-check everything" in text


def test_seeded_personas_have_personality(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    assert all(p["data"].get("personality") for p in store.list_personas())


def test_reroll_changes_personality(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    client = TestClient(create_app(store, background=False))
    client.post("/onboarding", data={"provider": "fake"})

    pid = store.list_personas()[0]["id"]
    before = store.get_persona(pid)["data"]["personality"]

    # Reroll a few times; at least one should differ (unseeded randomness).
    changed = False
    for _ in range(5):
        client.post(f"/personas/{pid}/reroll")
        if store.get_persona(pid)["data"]["personality"] != before:
            changed = True
            break
    assert changed
