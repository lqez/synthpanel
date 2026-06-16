import asyncio
from contextlib import asynccontextmanager

import pytest

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import FakeLLM
from synthpanel.orchestrator import PanelProgress, run_panel
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation, SessionStatus
from tests.fakes import FakeBrowser

pytestmark = pytest.mark.asyncio


def _personas(n):
    return [Persona(name=f"P{i}", intent=Intent(goal="g")) for i in range(n)]


class _Tracker:
    """Records how many sessions are active simultaneously."""

    def __init__(self):
        self.active = 0
        self.peak = 0

    @asynccontextmanager
    async def factory(self, persona):
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            await asyncio.sleep(0.01)  # hold the slot so overlap is observable
            yield FakeBrowser()
        finally:
            self.active -= 1


async def test_runs_all_and_preserves_order():
    tracker = _Tracker()
    llm = FakeLLM(script=[Action(type=ActionType.DONE)])
    results = await run_panel(_personas(5), tracker.factory, llm, concurrency=2, max_steps=3)
    assert [r.persona_name for r in results] == ["P0", "P1", "P2", "P3", "P4"]


async def test_concurrency_is_capped():
    tracker = _Tracker()
    llm = FakeLLM(script=[Action(type=ActionType.DONE)])
    await run_panel(_personas(6), tracker.factory, llm, concurrency=2, max_steps=3)
    assert tracker.peak <= 2
    assert tracker.peak == 2  # actually reaches the cap


class _AlwaysDone:
    """Stateless provider so it can be shared across concurrent sessions."""

    async def decide(self, turn):
        return Action(type=ActionType.DONE, rationale="done")


async def test_progress_events_emitted():
    events: list[PanelProgress] = []
    llm = _AlwaysDone()

    @asynccontextmanager
    async def factory(persona):
        yield FakeBrowser()

    await run_panel(
        _personas(3), factory, llm, concurrency=3, max_steps=2,
        on_progress=lambda e: events.append(e),
    )
    starts = [e for e in events if e.kind == "start"]
    finishes = [e for e in events if e.kind == "finish"]
    assert len(starts) == 3
    assert len(finishes) == 3
    assert all(e.status == "success" for e in finishes)


class _SlowAlwaysDone:
    """A session whose factory hangs longer than the session timeout."""

    @asynccontextmanager
    async def factory(self, persona):
        await asyncio.sleep(5)  # exceeds the timeout in the test
        yield FakeBrowser()


async def test_session_timeout_recorded_as_failed_bug():
    tracker = _SlowAlwaysDone()
    llm = _AlwaysDone()
    results = await run_panel(
        _personas(1), tracker.factory, llm, concurrency=1, max_steps=2,
        session_timeout=0.05,
    )
    assert results[0].status is SessionStatus.FAILED
    assert any("timed out" in b.title for b in results[0].bugs)


async def test_crash_is_retried_then_recorded():
    attempts = {"n": 0}

    @asynccontextmanager
    async def flaky_factory(persona):
        attempts["n"] += 1
        raise RuntimeError("boom")
        yield  # pragma: no cover

    results = await run_panel(
        _personas(1), flaky_factory, _AlwaysDone(), concurrency=1, max_steps=2, retries=2,
    )
    # 1 initial + 2 retries = 3 attempts, then recorded as a failed session.
    assert attempts["n"] == 3
    assert results[0].status is SessionStatus.FAILED
    assert any("crashed" in b.title for b in results[0].bugs)


async def test_artifact_paths_propagated_from_session():
    class _SessionWithArtifacts(FakeBrowser):
        trace_path = "/tmp/trace.zip"
        video_path = "/tmp/video.webm"

    @asynccontextmanager
    async def factory(persona):
        yield _SessionWithArtifacts()

    results = await run_panel(_personas(1), factory, _AlwaysDone(), max_steps=2)
    assert results[0].trace_path == "/tmp/trace.zip"
    assert results[0].video_path == "/tmp/video.webm"
