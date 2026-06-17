import pytest

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.loop import run_session
from synthpanel.agent.prompts import render_user_turn
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.languages import english_name, normalize
from synthpanel.report.models import Observation
from synthpanel.web.store import Store
from tests.fakes import FakeBrowser


def test_language_normalization():
    assert normalize("ko") == "ko"
    assert normalize(None) == "en"
    assert normalize("xx") == "en"
    assert english_name("ja") == "Japanese"


def test_prompt_carries_output_language():
    persona = Persona(name="Tester", intent=Intent(goal="g"))
    turn = Turn(
        persona=persona,
        observation=Observation(url="u"),
        history=[],
        step_idx=0,
        language="ko",
    )
    text = render_user_turn(turn)
    assert "OUTPUT LANGUAGE" in text
    assert "Korean" in text


@pytest.mark.asyncio
async def test_run_session_propagates_language_to_turn():
    seen = {}

    class _Capture:
        async def decide(self, turn):
            seen["language"] = turn.language
            return Action(type=ActionType.DONE)

    persona = Persona(name="Tester", intent=Intent(goal="g"))
    await run_session(persona, FakeBrowser(), _Capture(), max_steps=2, language="ja")
    assert seen["language"] == "ja"


def test_store_language_preference_and_project_fallback(tmp_path):
    s = Store(tmp_path / "db.sqlite")
    assert s.get_language() == "en"  # default
    s.set_language("ko")
    assert s.get_language() == "ko"

    # Project without an explicit language inherits the global default.
    pid = s.create_project("App", "https://app.test", "f", [])
    project = s.get_project(pid)
    assert project["language"] is None
    assert s.project_language(project) == "ko"

    # Project with an explicit language overrides the default.
    pid2 = s.create_project("App2", "https://app.test", "f", [], language="ja")
    assert s.project_language(s.get_project(pid2)) == "ja"
