"""SynthPanel CLI (early scaffolding).

`version` works offline. `run` drives a single persona with the Fake provider
against a real URL via Playwright; real LLM + parallel orchestration + reporting
land in later steps.
"""

from __future__ import annotations

import asyncio

import typer
from rich import print as rprint

from synthpanel import __version__
from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import FakeLLM
from synthpanel.agent.loop import run_session
from synthpanel.persona.models import Intent, Persona

app = typer.Typer(add_completion=False, help="LLM persona-driven usability testing.")


@app.command()
def version() -> None:
    """Print the SynthPanel version."""
    rprint(f"SynthPanel {__version__}")


@app.command()
def run(
    url: str = typer.Option(..., help="Target web app URL."),
    persona_name: str = typer.Option("Tester", help="Persona display name."),
    goal: str = typer.Option("Explore the app and reach the main feature.", help="Persona goal."),
    max_steps: int = typer.Option(10, help="Max steps before giving up."),
    provider: str = typer.Option("fake", help="LLM provider: fake | anthropic."),
    headless: bool = typer.Option(True, help="Run the browser headless."),
) -> None:
    """Run a single persona session against URL (scaffolding: fake provider only)."""
    if provider != "fake":
        raise typer.BadParameter("only the 'fake' provider is wired up so far")

    persona = Persona(name=persona_name, intent=Intent(goal=goal))
    result = asyncio.run(_run_one(url, persona, max_steps, headless))

    rprint(f"[bold]{result.persona_name}[/bold] -> {result.status.value}")
    rprint(f"steps: {len(result.steps)}, bugs: {len(result.bugs)}")
    for bug in result.bugs:
        rprint(f"  [red]BUG[/red] ({bug.severity.value}) {bug.title}")


async def _run_one(url: str, persona: Persona, max_steps: int, headless: bool):
    from playwright.async_api import async_playwright

    from synthpanel.browser.session import PlaywrightSession

    # A trivial exploratory script; the real LLM decides these from step 4 on.
    script = [
        Action(type=ActionType.SCROLL, rationale="Get an overview of the page."),
        Action(type=ActionType.WAIT, rationale="Let content settle."),
        Action(type=ActionType.DONE, rationale="Reached an overview of the app."),
    ]
    llm = FakeLLM(script=script, bug_on_console_error=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        try:
            async with PlaywrightSession.create(browser, url) as session:
                return await run_session(persona, session, llm, max_steps=max_steps)
        finally:
            await browser.close()


if __name__ == "__main__":
    app()
