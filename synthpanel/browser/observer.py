"""Format a page's accessibility tree for the LLM (DOM / accessibility mode).

Playwright's modern API is `Locator.aria_snapshot()`, which returns a YAML-ish
text tree of roles + accessible names (e.g. `- button "Sign in"`). That's already
LLM-friendly, so we only bound its size here. (The legacy
`page.accessibility.snapshot()` was removed in recent Playwright versions.)
"""

from __future__ import annotations


def format_aria_snapshot(snapshot: str | None, *, max_lines: int = 200) -> str:
    """Normalize and truncate an aria snapshot string for prompt inclusion."""
    if not snapshot or not snapshot.strip():
        return "(empty page)"
    lines = snapshot.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines] + ["… (truncated)"])
    return snapshot.strip()
