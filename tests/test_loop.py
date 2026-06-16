import pytest

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import FakeLLM
from synthpanel.agent.loop import run_session
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation, SessionStatus
from tests.fakes import FakeBrowser

pytestmark = pytest.mark.asyncio


def _persona() -> Persona:
    return Persona(name="Tester", intent=Intent(goal="reach the dashboard"))


async def test_reaches_goal_with_done():
    browser = FakeBrowser()
    llm = FakeLLM(
        script=[
            Action(type=ActionType.CLICK, target='button "Start"'),
            Action(type=ActionType.DONE, rationale="done"),
        ]
    )
    result = await run_session(_persona(), browser, llm, max_steps=10)
    assert result.status is SessionStatus.SUCCESS
    assert len(browser.executed) == 1
    assert result.steps[-1].action_type == "done"


async def test_give_up_when_script_exhausted():
    result = await run_session(_persona(), FakeBrowser(), FakeLLM(script=[]), max_steps=5)
    assert result.status is SessionStatus.GAVE_UP


async def test_console_error_becomes_bug():
    browser = FakeBrowser(
        observations=[Observation(url="https://app.test", console_errors=["TypeError: x"])]
    )
    llm = FakeLLM(bug_on_console_error=True)
    result = await run_session(_persona(), browser, llm, max_steps=1)
    assert len(result.bugs) == 1
    assert "Console errors" in result.bugs[0].title


async def test_browser_exception_recorded_as_bug():
    browser = FakeBrowser(fail_on=ActionType.CLICK)
    llm = FakeLLM(
        script=[
            Action(type=ActionType.CLICK, target='button "Broken"'),
            Action(type=ActionType.DONE),
        ]
    )
    result = await run_session(_persona(), browser, llm, max_steps=5)
    assert any("failed" in b.title for b in result.bugs)
    # Loop keeps going after the error and still reaches DONE.
    assert result.status is SessionStatus.SUCCESS


async def test_max_steps_terminates():
    # Script never ends in DONE; FakeLLM gives up only after script — but here we
    # use an infinite-feeling short script and a low cap to confirm the bound.
    browser = FakeBrowser()
    llm = FakeLLM(script=[Action(type=ActionType.SCROLL)] * 100)
    result = await run_session(_persona(), browser, llm, max_steps=3)
    assert len(result.steps) == 3
    assert result.status is SessionStatus.FAILED


async def test_typed_password_is_redacted_from_trace_and_history():
    from synthpanel.persona.identity import synthetic_identity

    persona = _persona()
    pw = synthetic_identity(persona).password
    browser = FakeBrowser()
    llm = FakeLLM(
        script=[
            Action(type=ActionType.TYPE, target='textbox "Password"', value=pw),
            Action(type=ActionType.DONE),
        ]
    )
    result = await run_session(persona, browser, llm, max_steps=5)

    type_step = result.steps[0]
    assert type_step.action_type == "type"
    # The real password must never appear in the stored trace.
    assert type_step.action_value == "***"
    assert pw not in (type_step.action_value or "")
    assert all(pw not in (s.observation_digest or "") for s in result.steps)


async def test_caller_supplied_secret_redacted():
    persona = _persona()
    browser = FakeBrowser()
    llm = FakeLLM(script=[Action(type=ActionType.TYPE, target="x", value="hunter2-secret")])
    result = await run_session(persona, browser, llm, max_steps=2, secrets={"hunter2-secret"})
    assert result.steps[0].action_value == "***"
