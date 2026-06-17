"""The Observe-Think-Act-Verify loop for a single persona session.

Provider-agnostic and browser-agnostic: it depends only on the LLMProvider and
BrowserSession protocols, so it runs identically in tests (Fake everything) and
production (Anthropic + Playwright). See PLAN.md section 2.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from synthpanel.agent.actions import TERMINAL_ACTIONS, Action, ActionType
from synthpanel.agent.llm import LLMProvider, Turn
from synthpanel.agent.prompts import render_user_turn
from synthpanel.browser.base import BrowserSession
from synthpanel.persona.identity import synthetic_identity
from synthpanel.persona.models import Persona
from synthpanel.report.models import (
    BugReport,
    SessionResult,
    SessionStatus,
    Severity,
    StepTrace,
)

StepSink = Callable[[int, str, str | None], Awaitable[None] | None]


async def run_session(
    persona: Persona,
    browser: BrowserSession,
    llm: LLMProvider,
    *,
    max_steps: int = 25,
    secrets: set[str] | None = None,
    language: str = "en",
    focus: str = "",
    on_step: StepSink | None = None,
) -> SessionResult:
    """Run one persona to its goal, giving up, or max_steps, and return results.

    Secrets (the persona's synthetic password plus any caller-supplied values) are
    redacted from step traces and history so credentials the persona types never
    land in stored output.
    """
    result = SessionResult(persona_name=persona.name, status=SessionStatus.FAILED)
    history: list[str] = []

    secret_values = {s for s in (secrets or set()) if s}
    identity = synthetic_identity(persona)
    if identity.password:
        secret_values.add(identity.password)

    for step_idx in range(max_steps):
        # --- Observe ---
        observation = await browser.observe()

        # --- Think ---
        turn = Turn(
            persona=persona,
            observation=observation,
            history=history,
            step_idx=step_idx,
            language=language,
            focus=focus,
        )
        llm_prompt = _redact(render_user_turn(turn), secret_values)
        llm_error: str | None = None
        try:
            action = await llm.decide(turn)
        except Exception as exc:  # noqa: BLE001
            llm_error = f"{type(exc).__name__}: {exc}"
            action = Action(type=ActionType.GIVE_UP, rationale=f"LLM error: {llm_error}")

        if on_step is not None:
            maybe = on_step(step_idx, action.type.value, observation.url)
            if asyncio.iscoroutine(maybe):
                await maybe

        trace = StepTrace(
            step_idx=step_idx,
            observation_digest=_redact(observation.digest(), secret_values),
            action_type=action.type.value,
            action_target=action.target,
            action_value=_redact(action.value, secret_values),
            rationale=action.rationale,
            llm_prompt=llm_prompt,
            llm_error=llm_error,
        )

        if llm_error:
            result.bugs.append(
                BugReport(
                    title=f"LLM 오류 (스텝 {step_idx})",
                    severity=Severity.CRITICAL,
                    actual=llm_error,
                    persona_name=persona.name,
                    step_idx=step_idx,
                )
            )

        # --- Act / Verify ---
        if action.type in TERMINAL_ACTIONS:
            result.status = (
                SessionStatus.SUCCESS
                if action.type is ActionType.DONE
                else SessionStatus.GAVE_UP
            )
            # Capture the persona's closing assessment as feedback.
            if action.value:
                result.ux_feedback += (_redact(action.value, secret_values) or "") + "\n"
            trace.result = action.type.value
            result.steps.append(trace)
            history.append(_summarize(action, trace.result, secret_values))
            break

        if action.type is ActionType.REPORT_BUG:
            result.bugs.append(_bug_from(action, observation, persona.name, step_idx))
            trace.result = "bug reported"
        elif action.type is ActionType.NOTE:
            result.ux_feedback += (_redact(action.value, secret_values) or "") + "\n"
            trace.result = "note recorded"
        else:
            try:
                trace.result = await browser.execute(action)
            except Exception as exc:  # noqa: BLE001 - surface as a bug, keep going
                trace.ok = False
                trace.result = f"error: {exc}"
                result.bugs.append(
                    BugReport(
                        title=f"Action '{action.type.value}' failed",
                        severity=Severity.MAJOR,
                        repro_steps=[h for h in history] + [_summarize(action, "", secret_values)],
                        actual=str(exc),
                        persona_name=persona.name,
                        step_idx=step_idx,
                        console_errors=observation.console_errors,
                    )
                )

        result.steps.append(trace)
        history.append(_summarize(action, trace.result, secret_values))

    return result


def _redact(text: str | None, secrets: set[str]) -> str | None:
    if not text:
        return text
    for secret in secrets:
        text = text.replace(secret, "***")
    return text


def _summarize(action: Action, outcome: str, secrets: set[str]) -> str:
    target = f" {action.target}" if action.target else ""
    redacted = _redact(action.value, secrets)
    value = f" = {redacted!r}" if redacted else ""
    return f"[{action.type.value}{target}{value}] -> {outcome}".strip()


def _bug_from(action: Action, observation, persona_name: str, step_idx: int) -> BugReport:
    return BugReport(
        title=action.value or "Issue reported by persona",
        severity=Severity.MAJOR,
        expected="",
        actual=action.rationale or action.value or "",
        persona_name=persona_name,
        step_idx=step_idx,
        screenshot_b64=observation.screenshot_b64,
        console_errors=observation.console_errors,
    )
