"""LLM provider abstraction.

The agent loop only depends on the `LLMProvider` protocol, so it runs identically
against the real Anthropic API or a deterministic `FakeLLM` in tests / offline.
See PLAN.md section 7.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from synthpanel.agent.actions import Action, ActionType
from synthpanel.persona.models import Persona
from synthpanel.report.models import Observation


class Turn(BaseModel):
    """One step's input to the LLM: the persona, the observation, and history."""

    persona: Persona
    observation: Observation
    history: list[str]
    step_idx: int
    # Language code the agent should write its notes/bugs/feedback in.
    language: str = "en"


@runtime_checkable
class LLMProvider(Protocol):
    """Decides the next Action given the current Turn."""

    async def decide(self, turn: Turn) -> Action:
        ...


class FakeLLM:
    """Deterministic provider for tests and offline runs.

    Replays a fixed script of actions; once exhausted it emits GIVE_UP so any
    loop terminates. A `bug_on` predicate lets tests trigger bug reports based on
    the live observation (e.g. when console errors appear).
    """

    def __init__(
        self,
        script: list[Action] | None = None,
        *,
        bug_on_console_error: bool = False,
    ) -> None:
        self._script = list(script or [])
        self._i = 0
        self._bug_on_console_error = bug_on_console_error

    async def decide(self, turn: Turn) -> Action:
        if self._bug_on_console_error and turn.observation.console_errors:
            return Action(
                type=ActionType.REPORT_BUG,
                value="Console errors detected on the page",
                rationale="Observed JavaScript console errors during interaction.",
            )
        if self._i < len(self._script):
            action = self._script[self._i]
            self._i += 1
            return action
        return Action(type=ActionType.GIVE_UP, rationale="Script exhausted.")
