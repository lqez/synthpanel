"""The BrowserSession protocol decouples the agent loop from Playwright.

The loop only needs to observe the page and execute browser actions. Tests use a
fake in-memory session; production uses the Playwright-backed PlaywrightSession.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from synthpanel.agent.actions import Action
from synthpanel.report.models import Observation


@runtime_checkable
class BrowserSession(Protocol):
    async def observe(self) -> Observation:
        """Capture the current page state as an Observation."""
        ...

    async def execute(self, action: Action) -> str:
        """Execute a browser action; return a short human-readable result.

        Raises on a fatal browser error (the loop converts that to a failed run).
        """
        ...
