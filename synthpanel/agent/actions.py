"""The action vocabulary the LLM chooses from each step.

This is the contract between the LLM (which emits an Action as JSON / tool-use)
and the browser layer (which executes it). See PLAN.md section 2.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    WAIT = "wait"
    ASSERT = "assert"
    NOTE = "note"            # subjective UX observation, not a page mutation
    REPORT_BUG = "report_bug"
    DONE = "done"            # goal achieved
    GIVE_UP = "give_up"      # persona quits in frustration


# Actions that end the session.
TERMINAL_ACTIONS = frozenset({ActionType.DONE, ActionType.GIVE_UP})

# Actions that drive the browser (vs. meta actions like note/report_bug/done).
BROWSER_ACTIONS = frozenset(
    {
        ActionType.CLICK,
        ActionType.TYPE,
        ActionType.NAVIGATE,
        ActionType.SCROLL,
        ActionType.WAIT,
        ActionType.ASSERT,
    }
)


class Action(BaseModel):
    """A single decision from the LLM."""

    type: ActionType
    # Stable accessibility ref (role + name) or selector for browser actions.
    target: str | None = None
    # Text to type, URL to navigate to, assertion text, note/bug body, etc.
    value: str | None = None
    rationale: str = Field(default="", description="Why the persona chose this.")
