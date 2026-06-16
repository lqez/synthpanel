"""Run a panel of personas in parallel, each in its own isolated session.

Concurrency is bounded by a semaphore to respect LLM rate limits and CPU. The
loop and browser are injected (session_factory + LLMProvider), so this is fully
testable offline. An optional progress callback receives session-level events,
which the web layer streams to the UI (SSE) in a later step.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncContextManager, Awaitable, Callable

from synthpanel.agent.llm import LLMProvider
from synthpanel.agent.loop import run_session
from synthpanel.browser.base import BrowserSession
from synthpanel.persona.models import Persona
from synthpanel.report.models import SessionResult

# Factory: given a persona, return an async context manager yielding its session.
SessionFactory = Callable[[Persona], AsyncContextManager[BrowserSession]]
# Progress sink: may be a plain or async callable.
ProgressSink = Callable[["PanelProgress"], Awaitable[None] | None]


@dataclass(frozen=True)
class PanelProgress:
    persona_name: str
    kind: str  # "start" | "finish"
    index: int
    total: int
    status: str | None = None


async def _emit(sink: ProgressSink | None, event: PanelProgress) -> None:
    if sink is None:
        return
    result = sink(event)
    if asyncio.iscoroutine(result):
        await result


async def run_panel(
    personas: list[Persona],
    session_factory: SessionFactory,
    llm: LLMProvider,
    *,
    concurrency: int = 4,
    max_steps: int = 15,
    on_progress: ProgressSink | None = None,
) -> list[SessionResult]:
    """Run every persona concurrently (capped), preserving input order in output."""
    total = len(personas)
    sem = asyncio.Semaphore(max(1, concurrency))
    results: list[SessionResult | None] = [None] * total

    async def worker(index: int, persona: Persona) -> None:
        async with sem:
            await _emit(on_progress, PanelProgress(persona.name, "start", index, total))
            async with session_factory(persona) as session:
                result = await run_session(persona, session, llm, max_steps=max_steps)
            results[index] = result
            await _emit(
                on_progress,
                PanelProgress(persona.name, "finish", index, total, status=result.status.value),
            )

    await asyncio.gather(*(worker(i, p) for i, p in enumerate(personas)))
    return [r for r in results if r is not None]
