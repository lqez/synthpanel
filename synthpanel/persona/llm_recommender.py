"""LLM-backed persona recommendation: Anthropic, OpenAI, and Ollama.

Each provider function asks the model for a structured JSON panel and validates
entries into Persona objects. Kept separate from the heuristic recommender so
that import stays lightweight when providers are unavailable.
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

# Anthropic tool format
_ANTHROPIC_TOOL = {
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

# OpenAI / Ollama function-calling format (same schema, different envelope)
_OAI_TOOL = {
    "type": "function",
    "function": {
        "name": "panel",
        "description": "Return the recommended panel of personas.",
        "parameters": _ANTHROPIC_TOOL["input_schema"],
    },
}


def _make_prompt(context: AppContext, n: int) -> str:
    parts = []
    if context.url:
        parts.append(f"App URL: {context.url}")
    parts.append(f"Testing focus: {context.focus or '(general usability)'}")
    parts.append(f"Recommend exactly {n} personas.")
    return "\n".join(parts)


async def recommend_with_anthropic(context: AppContext, n: int, config: dict) -> list[Persona]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=config["api_key"])
    model = config.get("model") or "claude-opus-4-8"
    msg = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=_SYSTEM,
        tools=[_ANTHROPIC_TOOL],
        tool_choice={"type": "tool", "name": "panel"},
        messages=[{"role": "user", "content": _make_prompt(context, n)}],
    )
    for block in msg.content:
        if getattr(block, "type", "") == "tool_use":
            return _to_personas(block.input.get("personas", []))
    return []


async def recommend_with_openai(context: AppContext, n: int, config: dict) -> list[Persona]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("base_url") or None,
    )
    model = config.get("model") or "gpt-4o"
    resp = await client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _make_prompt(context, n)},
        ],
        tools=[_OAI_TOOL],
        tool_choice={"type": "function", "function": {"name": "panel"}},
    )
    for call in (resp.choices[0].message.tool_calls or []):
        if call.function.name == "panel":
            try:
                return _to_personas(json.loads(call.function.arguments).get("personas", []))
            except Exception:  # noqa: BLE001
                continue
    return []


async def recommend_with_ollama(context: AppContext, n: int, config: dict) -> list[Persona]:
    from ollama import AsyncClient

    client = AsyncClient(
        host=config.get("base_url") or "http://localhost:11434",
        timeout=300.0,
    )
    model = config.get("model") or "llama3.1"
    resp = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _make_prompt(context, n)},
        ],
        tools=[_OAI_TOOL],
    )
    for call in (getattr(resp.message, "tool_calls", None) or []):
        if getattr(call.function, "name", "") == "panel":
            args = call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            try:
                return _to_personas(args.get("personas", []))
            except Exception:  # noqa: BLE001
                continue
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
