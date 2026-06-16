"""Serialize a Playwright page into an Observation (DOM / accessibility mode).

Imports of `playwright` are deferred to call sites so the package (and the test
suite) import cleanly without Playwright installed.
"""

from __future__ import annotations

from typing import Any

from synthpanel.report.models import Observation


def serialize_a11y_tree(snapshot: dict[str, Any] | None, *, max_lines: int = 200) -> str:
    """Flatten Playwright's accessibility snapshot into indented role+name text.

    Each interactive node is rendered as `role "name"` so the LLM can reference
    it stably. Truncated to `max_lines` to bound token cost.
    """
    if not snapshot:
        return "(empty page)"

    lines: list[str] = []

    def walk(node: dict[str, Any], depth: int) -> None:
        if len(lines) >= max_lines:
            return
        role = node.get("role", "")
        name = node.get("name", "")
        if role:
            rendered = f'{"  " * depth}{role}'
            if name:
                rendered += f' "{name}"'
            lines.append(rendered)
            depth += 1
        for child in node.get("children", []) or []:
            walk(child, depth)

    walk(snapshot, 0)
    if len(lines) >= max_lines:
        lines.append("… (truncated)")
    return "\n".join(lines)
