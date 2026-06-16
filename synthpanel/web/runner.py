"""Execute a project's usability test: run each persona against the target URL.

Sequential for now (parallel orchestrator is a later step). Builds the LLM
provider from saved settings and drives Playwright sessions. Any failure to
launch the browser is captured into the run result rather than raised, so the
web UI always gets a result to display.
"""

from __future__ import annotations

from synthpanel.agent.loop import run_session
from synthpanel.agent.providers import build_provider
from synthpanel.persona.models import Persona
from synthpanel.report.models import SessionResult, SessionStatus


async def execute_run(project: dict, settings: dict, *, max_steps: int = 15) -> dict:
    """Run all personas in `project` and return a serializable result dict."""
    personas = [Persona.model_validate(p) for p in project.get("personas", [])]
    if not personas:
        personas = [_default_persona(project)]

    provider = build_provider(settings["provider"], settings["config"])

    try:
        results = await _run_with_playwright(
            project["url"], personas, provider, max_steps
        )
    except Exception as exc:  # noqa: BLE001 - surface launch/setup errors in the UI
        return {
            "error": f"{type(exc).__name__}: {exc}",
            "sessions": [],
            "summary": {"personas": len(personas), "bugs": 0},
        }

    total_bugs = sum(len(r.bugs) for r in results)
    return {
        "sessions": [r.model_dump() for r in results],
        "summary": {
            "personas": len(results),
            "bugs": total_bugs,
            "succeeded": sum(1 for r in results if r.status is SessionStatus.SUCCESS),
        },
    }


async def _run_with_playwright(
    url: str, personas: list[Persona], provider, max_steps: int
) -> list[SessionResult]:
    from playwright.async_api import async_playwright

    from synthpanel.browser.session import PlaywrightSession

    results: list[SessionResult] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            for persona in personas:
                async with PlaywrightSession.create(browser, url) as session:
                    results.append(
                        await run_session(persona, session, provider, max_steps=max_steps)
                    )
        finally:
            await browser.close()
    return results


def _default_persona(project: dict) -> Persona:
    from synthpanel.persona.models import Intent

    goal = project.get("focus") or "Explore the app and reach the main feature."
    return Persona(name="Default Tester", intent=Intent(goal=goal))
