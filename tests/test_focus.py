import pytest

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.loop import run_session
from synthpanel.agent.prompts import render_user_turn
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation, SessionResult, SessionStatus
from synthpanel.web import runner
from tests.fakes import FakeBrowser


def _turn(focus=""):
    return Turn(
        persona=Persona(name="x", intent=Intent(goal="g")),
        observation=Observation(url="u"),
        history=[],
        step_idx=0,
        focus=focus,
    )


def test_prompt_includes_focus_when_set():
    text = render_user_turn(_turn(focus="check the checkout flow"))
    assert "TEST FOCUS" in text
    assert "check the checkout flow" in text


def test_prompt_omits_focus_when_blank():
    assert "TEST FOCUS" not in render_user_turn(_turn(focus="   "))


@pytest.mark.asyncio
async def test_run_session_propagates_focus_to_turn():
    seen = {}

    class _Capture:
        async def decide(self, turn):
            seen["focus"] = turn.focus
            return Action(type=ActionType.DONE)

    persona = Persona(name="x", intent=Intent(goal="g"))
    await run_session(persona, FakeBrowser(), _Capture(), max_steps=2, focus="mobile a11y")
    assert seen["focus"] == "mobile a11y"


@pytest.mark.asyncio
async def test_runner_passes_project_focus(monkeypatch):
    captured = {}

    async def fake_run(url, personas, provider, **kwargs):
        captured["focus"] = kwargs.get("focus")
        return [SessionResult(persona_name="A", status=SessionStatus.SUCCESS)]

    monkeypatch.setattr(runner, "_run_with_playwright", fake_run)
    await runner.execute_run(
        {"url": "u", "personas": [{"name": "A", "intent": {"goal": "g"}}]},
        {"provider": "fake", "config": {}},
        focus="signup errors",
    )
    assert captured["focus"] == "signup errors"
