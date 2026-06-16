import asyncio
from contextlib import asynccontextmanager

import pytest

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import FakeLLM
from synthpanel.orchestrator import PanelProgress, run_panel
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation
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
