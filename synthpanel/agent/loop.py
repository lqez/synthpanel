"""The Observe-Think-Act-Verify loop for a single persona session.

Provider-agnostic and browser-agnostic: it depends only on the LLMProvider and
BrowserSession protocols, so it runs identically in tests (Fake everything) and
production (Anthropic + Playwright). See PLAN.md section 2.
"""

from __future__ import annotations

from synthpanel.agent.actions import TERMINAL_ACTIONS, Action, ActionType
from synthpanel.agent.llm import LLMProvider, Turn
from synthpanel.browser.base import BrowserSession
from synthpanel.persona.models import Persona
from synthpanel.report.models import (
    BugReport,
    SessionResult,
    SessionStatus,
    Severity,
    StepTrace,
)


async def run_session(
    persona: Persona,
    browser: BrowserSession,
    llm: LLMProvider,
    *,
    max_steps: int = 25,
) -> SessionResult:
    """Run one persona to its goal, giving up, or max_steps, and return results."""
    result = SessionResult(persona_name=persona.name, status=SessionStatus.FAILED)
    history: list[str] = []

    for step_idx in range(max_steps):
        # --- Observe ---
        observation = await browser.observe()

        # --- Think ---
        turn = Turn(
            persona=persona,
            observation=observation,
            history=history,
            step_idx=step_idx,
        )
        action = await llm.decide(turn)

        trace = StepTrace(
            step_idx=step_idx,
            observation_digest=observation.digest(),
            action_type=action.type.value,
            action_target=action.target,
            action_value=action.value,
            rationale=action.rationale,
        )

        # --- Act / Verify ---
        if action.type in TERMINAL_ACTIONS:
            result.status = (
                SessionStatus.SUCCESS
                if action.type is ActionType.DONE
                else SessionStatus.GAVE_UP
            )
            trace.result = action.type.value
            result.steps.append(trace)
            history.append(_summarize(action, trace.result))
            break

        if action.type is ActionType.REPORT_BUG:
            result.bugs.append(_bug_from(action, observation, persona.name, step_idx))
            trace.result = "bug reported"
        elif action.type is ActionType.NOTE:
            result.ux_feedback += (action.value or "") + "\n"
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
                        repro_steps=[h for h in history] + [_summarize(action, "")],
                        actual=str(exc),
                        persona_name=persona.name,
                        step_idx=step_idx,
                        console_errors=observation.console_errors,
                    )
                )

        result.steps.append(trace)
        history.append(_summarize(action, trace.result))

    return result


def _summarize(action: Action, outcome: str) -> str:
    target = f" {action.target}" if action.target else ""
    value = f" = {action.value!r}" if action.value else ""
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
