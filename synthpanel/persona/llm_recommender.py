"""Anthropic-backed persona recommendation (used when the provider is Claude).

Asks the model for a JSON panel and validates each entry into a Persona. Kept
separate so the heuristic recommender stays import-light and offline-safe.
"""

from __future__ import annotations

import json

from synthpanel.persona.models import Intent, Persona
from synthpanel.persona.recommender import AppContext

_SYSTEM = """\
You design a balanced panel of realistic user personas for usability-testing a \
web app. Cover the likely audience AND deliberate edge cases: low tech literacy, \
elderly users, accessibility needs (screen readers), slow networks. Make each \
persona believable, never a caricature. Each persona must have a concrete goal \
tied to the app's focus.
"""

_TOOL = {
    "name": "panel",
    "description": "Return the recommended panel of personas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "personas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "archetype": {"type": "string"},
                        "goal": {"type": "string"},
                        "demographics": {"type": "object"},
                        "tech": {"type": "object"},
                        "psych": {"type": "object"},
                        "attitudes": {"type": "object"},
                    },
                    "required": ["name", "goal"],
                },
            }
        },
        "required": ["personas"],
    },
}


async def recommend_with_anthropic(context: AppContext, n: int, config: dict) -> list[Persona]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=config["api_key"])
    model = config.get("model") or "claude-opus-4-8"
    prompt = (
        f"App URL: {context.url}\n"
        f"Testing focus: {context.focus or '(general usability)'}\n"
        f"Recommend exactly {n} personas."
    )
    msg = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "panel"},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in msg.content:
        if getattr(block, "type", "") == "tool_use":
            return _to_personas(block.input.get("personas", []))
    return []


def _to_personas(raw: list[dict]) -> list[Persona]:
    out: list[Persona] = []
    for item in raw:
        goal = item.get("goal") or "Explore the app."
        data = {k: v for k, v in item.items() if k != "goal"}
        data["intent"] = Intent(goal=goal)
        try:
            out.append(Persona.model_validate(data))
        except Exception:  # noqa: BLE001 - skip malformed entries, keep the rest
            continue
    return out
