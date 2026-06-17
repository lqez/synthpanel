"""Execute a project's usability test: run each persona against the target URL.

Builds the LLM provider from saved settings and drives parallel Playwright
sessions via the orchestrator. Per-session timeout and retry keep one stuck or
flaky persona from hanging or sinking the run. When `artifacts_dir` is given,
each session records a Playwright trace.zip + video for debugging. Token usage
and estimated cost are rolled into the run summary. Any failure to launch the
browser is captured into the result rather than raised, so the web UI always
gets something to display.
"""

from __future__ import annotations

from pathlib import Path

from synthpanel.agent.providers import build_provider
from synthpanel.orchestrator import ProgressSink, run_panel
from synthpanel.persona.models import Persona
from synthpanel.report.models import SessionResult, SessionStatus
from synthpanel.report.pricing import estimate_cost


async def execute_run(
    project: dict,
    settings: dict,
    *,
    max_steps: int = 15,
    concurrency: int = 4,
    session_timeout: float | None = 600.0,
    retries: int = 1,
    language: str = "en",
    artifacts_dir: str | Path | None = None,
    on_progress: ProgressSink | None = None,
) -> dict:
    """Run all personas in `project` (in parallel) and return a result dict."""
    personas = [Persona.model_validate(p) for p in project.get("personas", [])]
    if not personas:
        personas = [_default_persona(project)]

    provider = build_provider(settings["provider"], settings["config"])

    try:
        results = await _run_with_playwright(
            project["url"],
            personas,
            provider,
            max_steps=max_steps,
            concurrency=concurrency,
            session_timeout=session_timeout,
            retries=retries,
            language=language,
            focus=project.get("focus", ""),
            artifacts_dir=Path(artifacts_dir) if artifacts_dir else None,
            on_progress=on_progress,
        )
    except Exception as exc:  # noqa: BLE001 - surface launch/setup errors in the UI
        return {
            "error": f"{type(exc).__name__}: {exc}",
            "sessions": [],
            "summary": {"personas": len(personas), "bugs": 0},
        }

    return {
        "sessions": [r.model_dump() for r in results],
        "summary": _summarize(results, provider),
    }


def _summarize(results: list[SessionResult], provider) -> dict:
    usage = getattr(provider, "usage", None) or {"input": 0, "output": 0}
    model = getattr(provider, "model", None)
    return {
        "personas": len(results),
        "bugs": sum(len(r.bugs) for r in results),
        "succeeded": sum(1 for r in results if r.status is SessionStatus.SUCCESS),
        "tokens_in": usage.get("input", 0),
        "tokens_out": usage.get("output", 0),
        "cost_usd": round(estimate_cost(model, usage.get("input", 0), usage.get("output", 0)), 4),
    }


async def _run_with_playwright(
    url: str,
    personas: list[Persona],
    provider,
    *,
    max_steps: int,
    concurrency: int,
    session_timeout: float | None,
    retries: int,
    language: str,
    focus: str,
    artifacts_dir: Path | None,
    on_progress: ProgressSink | None,
) -> list[SessionResult]:
    from playwright.async_api import async_playwright

    from synthpanel.browser.session import PlaywrightSession

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            def session_factory(persona):
                # Each persona gets its own isolated BrowserContext + artifacts dir.
                adir = artifacts_dir / _slug(persona.name) if artifacts_dir else None
                return PlaywrightSession.create(
                    browser,
                    url,
                    artifacts_dir=adir,
                    trace=adir is not None,
                    record_video=adir is not None,
                )

            return await run_panel(
                personas,
                session_factory,
                provider,
                concurrency=concurrency,
                max_steps=max_steps,
                session_timeout=session_timeout,
                retries=retries,
                language=language,
                focus=focus,
                on_progress=on_progress,
            )
        finally:
            await browser.close()


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:40] or "persona"


def _default_persona(project: dict) -> Persona:
    from synthpanel.persona.models import Intent

    goal = project.get("focus") or "Explore the app and reach the main feature."
    return Persona(name="Default Tester", intent=Intent(goal=goal))
