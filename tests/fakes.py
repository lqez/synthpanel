"""In-memory fakes so the agent loop runs without Playwright or a network."""

from __future__ import annotations

from synthpanel.agent.actions import Action, ActionType
from synthpanel.report.models import Observation


class FakeBrowser:
    """A scripted page: returns queued observations and records executed actions.

    Pass `fail_on` to simulate a fatal browser error for a given action type
    (e.g. a click on a broken element), which the loop should turn into a bug.
    """

    def __init__(
        self,
        observations: list[Observation] | None = None,
        *,
        fail_on: ActionType | None = None,
    ) -> None:
        self._observations = list(observations or [Observation(url="https://app.test")])
        self._i = 0
        self._fail_on = fail_on
        self.executed: list[Action] = []

    async def observe(self) -> Observation:
        obs = self._observations[min(self._i, len(self._observations) - 1)]
        self._i += 1
        return obs

    async def execute(self, action: Action) -> str:
        if self._fail_on is not None and action.type is self._fail_on:
            raise RuntimeError(f"element not found for {action.type.value}")
        self.executed.append(action)
        return f"ok:{action.type.value}"
