"""Run a panel of personas in parallel, each in its own isolated session.

Concurrency is bounded by a semaphore to respect LLM rate limits and CPU. Each
session can have a wall-clock timeout and a retry budget so one stuck or flaky
persona doesn't hang or sink the whole run. The loop and browser are injected
(session_factory + LLMProvider), so this is fully testable offline. An optional
progress callback receives session-level events, which the web layer streams to
the UI via SSE.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncContextManager, Awaitable, Callable

from synthpanel.agent.llm import LLMProvider
from synthpanel.agent.loop import run_session
from synthpanel.browser.base import BrowserSession
from synthpanel.persona.models import Persona
from synthpanel.report.models import BugReport, SessionResult, SessionStatus, Severity

# Factory: given a persona, return an async context manager yielding its session.
SessionFactory = Callable[[Persona], AsyncContextManager[BrowserSession]]
# Progress sink: may be a plain or async callable.
ProgressSink = Callable[["PanelProgress"], Awaitable[None] | None]


@dataclass(frozen=True)
class PanelProgress:
    persona_name: str
    kind: str  # "queue" | "start" | "step" | "finish"
    index: int
    total: int
    status: str | None = None
    step_idx: int | None = None
    action_type: str | None = None
    action_target: str | None = None
    rationale: str | None = None
    url: str | None = None


async def _emit(sink: ProgressSink | None, event: PanelProgress) -> None:
    if sink is None:
        return
    result = sink(event)
    if asyncio.iscoroutine(result):
        await result


async def _run_once(
    persona: Persona,
    session_factory: SessionFactory,
    llm: LLMProvider,
    max_steps: int,
    language: str,
    focus: str,
    on_progress: ProgressSink | None = None,
    index: int = 0,
    total: int = 1,
) -> SessionResult:
    async def _on_step(
        step_idx: int, action_type: str, url: str | None,
        action_target: str | None = None, rationale: str | None = None,
    ) -> None:
        await _emit(
            on_progress,
            PanelProgress(
                persona.name, "step", index, total,
                step_idx=step_idx, action_type=action_type,
                action_target=action_target, rationale=rationale, url=url,
            ),
        )

    async with session_factory(persona) as session:
        result = await run_session(
            persona, session, llm, max_steps=max_steps, language=language, focus=focus,
            on_step=_on_step,
        )
    # __aexit__ has run, so any trace path written on teardown is now available.
    result.trace_path = getattr(session, "trace_path", None)
    result.video_path = getattr(session, "video_path", None)
    return result


async def run_panel(
    personas: list[Persona],
    session_factory: SessionFactory,
    llm: LLMProvider,
    *,
    concurrency: int = 4,
    max_steps: int = 15,
    session_timeout: float | None = None,
    retries: int = 0,
    language: str = "en",
    focus: str = "",
    on_progress: ProgressSink | None = None,
) -> list[SessionResult]:
    """Run every persona concurrently (capped), preserving input order in output.

    `session_timeout` bounds each session's wall-clock time; a timeout is recorded
    as a failed session with a bug rather than aborting the run. `retries` re-runs
    a session that crashes (not one that times out) up to N extra times.
    """
    total = len(personas)
    sem = asyncio.Semaphore(max(1, concurrency))
    results: list[SessionResult | None] = [None] * total

    async def worker(index: int, persona: Persona) -> None:
        async def run_with_timeout(p: Persona) -> SessionResult:
            coro = _run_once(p, session_factory, llm, max_steps, language, focus, on_progress, index, total)
            if session_timeout is not None:
                return await asyncio.wait_for(coro, timeout=session_timeout)
            return await coro

        await _emit(on_progress, PanelProgress(persona.name, "queue", index, total))
        async with sem:
            await _emit(on_progress, PanelProgress(persona.name, "start", index, total))
            result = await _attempt(persona, run_with_timeout, retries)
            results[index] = result
            await _emit(
                on_progress,
                PanelProgress(persona.name, "finish", index, total, status=result.status.value),
            )

    await asyncio.gather(*(worker(i, p) for i, p in enumerate(personas)))
    return [r for r in results if r is not None]


async def _attempt(persona, run, retries: int) -> SessionResult:
    """Run a session, retrying crashes (but not timeouts) up to `retries` times."""
    last_exc: Exception | None = None
    for _ in range(retries + 1):
        try:
            return await run(persona)
        except asyncio.TimeoutError:
            return _failed(persona.name, "Session timed out", Severity.MAJOR)
        except Exception as exc:  # noqa: BLE001 - record + maybe retry
            last_exc = exc
    return _failed(persona.name, f"Session crashed: {last_exc}", Severity.CRITICAL)


def _failed(persona_name: str, title: str, severity: Severity) -> SessionResult:
    return SessionResult(
        persona_name=persona_name,
        status=SessionStatus.FAILED,
        bugs=[BugReport(title=title, severity=severity, persona_name=persona_name)],
    )
