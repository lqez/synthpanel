"""Playwright-backed BrowserSession: one isolated BrowserContext per persona.

This module imports Playwright lazily so the rest of the package stays importable
without it. Construct via `PlaywrightSession.create(...)` as an async context
manager. It captures console / page / failed-request errors as they happen and
folds them into each Observation.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from synthpanel.agent.actions import Action, ActionType
from synthpanel.browser.observer import format_aria_snapshot
from synthpanel.report.models import Observation

if TYPE_CHECKING:  # pragma: no cover
    from playwright.async_api import BrowserContext, Page


class PlaywrightSession:
    """Drives a single isolated page for one persona."""

    def __init__(self, context: "BrowserContext", page: "Page", *, vision: bool = False) -> None:
        self._context = context
        self._page = page
        self._vision = vision
        self._console_errors: list[str] = []
        self._page_errors: list[str] = []
        self._network_errors: list[str] = []
        self._wire_listeners()

    @classmethod
    @asynccontextmanager
    async def create(
        cls,
        browser: object,
        url: str,
        *,
        vision: bool = False,
        **context_kwargs: object,
    ) -> "AsyncIterator[PlaywrightSession]":
        """Create an isolated context+page, navigate to `url`, yield the session."""
        context = await browser.new_context(**context_kwargs)  # type: ignore[attr-defined]
        page = await context.new_page()
        session = cls(context, page, vision=vision)
        try:
            await page.goto(url)
            yield session
        finally:
            await context.close()

    def _wire_listeners(self) -> None:
        def on_console(msg: object) -> None:
            if getattr(msg, "type", "") == "error":
                self._console_errors.append(str(getattr(msg, "text", msg)))

        def on_page_error(exc: object) -> None:
            self._page_errors.append(str(exc))

        def on_request_failed(request: object) -> None:
            failure = getattr(request, "failure", None)
            url = getattr(request, "url", "")
            self._network_errors.append(f"{url} ({failure})")

        self._page.on("console", on_console)
        self._page.on("pageerror", on_page_error)
        self._page.on("requestfailed", on_request_failed)

    async def observe(self) -> Observation:
        snapshot = await self._page.locator("body").aria_snapshot()
        screenshot_b64 = None
        if self._vision:
            import base64

            png = await self._page.screenshot()
            screenshot_b64 = base64.b64encode(png).decode("ascii")
        return Observation(
            url=self._page.url,
            title=await self._page.title(),
            a11y_tree=format_aria_snapshot(snapshot),
            console_errors=list(self._console_errors),
            page_errors=list(self._page_errors),
            network_errors=list(self._network_errors),
            screenshot_b64=screenshot_b64,
        )

    async def execute(self, action: Action) -> str:
        page = self._page
        if action.type is ActionType.NAVIGATE and action.value:
            await page.goto(action.value)
            return f"navigated to {action.value}"
        if action.type is ActionType.CLICK and action.target:
            await self._locate(action.target).click(timeout=5000)
            return f"clicked {action.target}"
        if action.type is ActionType.TYPE and action.target:
            await self._locate(action.target).fill(action.value or "", timeout=5000)
            return f"typed into {action.target}"
        if action.type is ActionType.SCROLL:
            await page.mouse.wheel(0, 600)
            return "scrolled down"
        if action.type is ActionType.WAIT:
            await page.wait_for_timeout(1000)
            return "waited"
        if action.type is ActionType.ASSERT and action.value:
            visible = await self._locate(action.value).first.is_visible()
            return f"assert visible '{action.value}': {visible}"
        return f"no-op for {action.type}"

    def _locate(self, target: str):
        """Best-effort locator: try get_by_text, fall back to a CSS/selector."""
        page = self._page
        # Prefer role-name style refs like: button "Sign in"
        if '"' in target:
            role, _, name = target.partition('"')
            name = name.strip('"')
            role = role.strip()
            if role:
                return page.get_by_role(role, name=name)  # type: ignore[arg-type]
        return page.locator(target)
