"""Data models shared between the browser, the agent loop, and reporting.

Kept in one place so the agent loop can emit them and reporting can consume them
without a dependency cycle. See PLAN.md sections 4 and 6.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class SessionStatus(str, Enum):
    SUCCESS = "success"   # persona reached its goal
    FAILED = "failed"     # terminated on a fatal error / max steps
    GAVE_UP = "gaveup"    # persona chose to give up


class Observation(BaseModel):
    """A serialized snapshot of the page handed to the LLM each step."""

    url: str
    title: str = ""
    # Accessibility-tree text serialization (role + name + ref), DOM mode.
    a11y_tree: str = ""
    console_errors: list[str] = Field(default_factory=list)
    network_errors: list[str] = Field(default_factory=list)
    page_errors: list[str] = Field(default_factory=list)
    # Base64 PNG, only populated in vision mode.
    screenshot_b64: str | None = None

    def digest(self, limit: int = 2000) -> str:
        """Compact human/LLM-readable digest of the observation."""
        parts = [f"URL: {self.url}", f"TITLE: {self.title}"]
        if self.console_errors:
            parts.append("CONSOLE_ERRORS:\n" + "\n".join(self.console_errors))
        if self.network_errors:
            parts.append("NETWORK_ERRORS:\n" + "\n".join(self.network_errors))
        if self.page_errors:
            parts.append("PAGE_ERRORS:\n" + "\n".join(self.page_errors))
        parts.append("ACCESSIBILITY_TREE:\n" + self.a11y_tree[:limit])
        return "\n\n".join(parts)


class BugReport(BaseModel):
    title: str
    severity: Severity = Severity.MAJOR
    repro_steps: list[str] = Field(default_factory=list)
    expected: str = ""
    actual: str = ""
    persona_name: str = ""
    step_idx: int | None = None
    screenshot_b64: str | None = None
    console_errors: list[str] = Field(default_factory=list)


class StepTrace(BaseModel):
    step_idx: int
    observation_digest: str
    action_type: str
    action_target: str | None = None
    action_value: str | None = None
    rationale: str = ""
    result: str = ""
    ok: bool = True
    llm_prompt: str | None = None   # full user-turn text sent to the LLM
    llm_error: str | None = None    # exception message if the LLM call failed


class SessionResult(BaseModel):
    persona_name: str
    status: SessionStatus
    steps: list[StepTrace] = Field(default_factory=list)
    bugs: list[BugReport] = Field(default_factory=list)
    ux_feedback: str = ""
    # Filesystem paths to debugging artifacts, when captured.
    trace_path: str | None = None
    video_path: str | None = None
