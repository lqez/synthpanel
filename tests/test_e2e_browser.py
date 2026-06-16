"""End-to-end: drive a real Chromium page through the full stack.

Proves the integration the unit tests stub out — accessibility-tree observation,
action execution (click/type), and console-error capture — against a real page.
Run with `pytest -m e2e` (deselected by default). Skips cleanly if Chromium
isn't installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import FakeLLM
from synthpanel.agent.loop import run_session
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import SessionStatus

pytestmark = pytest.mark.e2e

_PAGE = """<!doctype html><html><head><title>Demo App</title></head><body>
  <h1>Demo App</h1>
  <button onclick="document.getElementById('out').textContent='Clicked!'">Start</button>
  <input aria-label="Email" />
  <h2 id="out"></h2>
  <script>console.error("intentional boom");</script>
</body></html>"""


@pytest.fixture()
async def browser():
    try:
        from playwright.async_api import async_playwright
    except ImportError:  # pragma: no cover
        pytest.skip("playwright not installed")

    pw = await async_playwright().start()
    try:
        br = await pw.chromium.launch(headless=True)
    except Exception as exc:  # pragma: no cover - browser binary missing
        await pw.stop()
        pytest.skip(f"chromium unavailable: {exc}")
    yield br
    await br.close()
    await pw.stop()


async def test_full_session_against_real_page(browser, tmp_path):
    from synthpanel.browser.session import PlaywrightSession

    page_file = tmp_path / "demo.html"
    page_file.write_text(_PAGE, encoding="utf-8")
    url = page_file.as_uri()

    persona = Persona(name="E2E", intent=Intent(goal="click start and enter email"))
    llm = FakeLLM(
        script=[
            Action(type=ActionType.CLICK, target='button "Start"'),
            Action(type=ActionType.TYPE, target='textbox "Email"', value="a@b.com"),
            Action(type=ActionType.DONE),
        ]
    )

    async with PlaywrightSession.create(browser, url) as session:
        before = await session.observe()
        # Observation reflects the real accessibility tree and captured console error.
        assert 'button "Start"' in before.a11y_tree
        assert any("boom" in e for e in before.console_errors)

        result = await run_session(persona, session, llm, max_steps=5)

        after = await session.observe()
        # The click actually mutated the page (heading now shows "Clicked!").
        assert 'heading "Clicked!"' in after.a11y_tree

    assert result.status is SessionStatus.SUCCESS
    actions = [s.action_type for s in result.steps]
    assert actions == ["click", "type", "done"]
    assert all(s.ok for s in result.steps)
