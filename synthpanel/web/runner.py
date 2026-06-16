"""Execute a project's usability test: run each persona against the target URL.

Sequential for now (parallel orchestrator is a later step). Builds the LLM
provider from saved settings and drives Playwright sessions. Any failure to
launch the browser is captured into the run result rather than raised, so the
web UI always gets a result to display.
"""

from __future__ import annotations

from synthpanel.agent.providers import build_provider
from synthpanel.orchestrator import ProgressSink, run_panel
from synthpanel.persona.models import Persona
from synthpanel.report.models import SessionResult, SessionStatus


async def execute_run(
    project: dict,
    settings: dict,
    *,
    max_steps: int = 15,
    concurrency: int = 4,
    on_progress: ProgressSink | None = None,
) -> dict:
    """Run all personas in `project` (in parallel) and return a result dict."""
    personas = [Persona.model_validate(p) for p in project.get("personas", [])]
    if not personas:
        personas = [_default_persona(project)]

    provider = build_provider(settings["provider"], settings["config"])

    try:
        results = await _run_with_playwright(
            project["url"], personas, provider, max_steps, concurrency, on_progress
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
    url: str,
    personas: list[Persona],
    provider,
    max_steps: int,
    concurrency: int,
    on_progress: ProgressSink | None,
) -> list[SessionResult]:
    from playwright.async_api import async_playwright

    from synthpanel.browser.session import PlaywrightSession

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            def session_factory(_persona):
                # Each persona gets its own isolated BrowserContext.
                return PlaywrightSession.create(browser, url)

            return await run_panel(
                personas,
                session_factory,
                provider,
                concurrency=concurrency,
                max_steps=max_steps,
                on_progress=on_progress,
            )
        finally:
            await browser.close()


def _default_persona(project: dict) -> Persona:
    from synthpanel.persona.models import Intent

    goal = project.get("focus") or "Explore the app and reach the main feature."
    return Persona(name="Default Tester", intent=Intent(goal=goal))
