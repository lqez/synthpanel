"""LLM-backed persona work: tag prioritization (fast) and full generation.

Two distinct jobs, both kept out of the heuristic recommender so imports stay
light when no provider is installed:

* prioritize_with_* — the fast recommendation path. The model only ranks which
  *tags* matter for a testing focus (a handful of short strings), so it returns
  quickly even on a flagship model. Selection from the library is done locally.
* recommend_with_* — full persona generation for the "create new persona" flow,
  where the model authors brand-new personas from a description.
"""

from __future__ import annotations

import json

from synthpanel.persona.models import Intent, Persona
from synthpanel.persona.recommender import AppContext
from synthpanel.persona.tags import TAG_KEYS, TAGS

# ── Tag prioritization (fast recommendation path) ──────────────────────────────

_PRIORITIZE_SYSTEM = """\
You help assemble a usability-testing panel. Given a testing focus and a fixed \
list of persona tags, return the tags most worth prioritizing for that focus, \
MOST IMPORTANT FIRST. Prefer tags that stress the focus, and include realistic \
edge cases (low tech literacy, elderly, accessibility needs, slow networks) when \
relevant. Use only tags from the provided list.\
"""

_PRIORITIZE_SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string", "enum": TAG_KEYS},
            "description": "Tag keys, most important first.",
        }
    },
    "required": ["tags"],
}

_ANTHROPIC_PRIORITIZE_TOOL = {
    "name": "prioritize",
    "description": "Return persona tags to prioritize for the testing focus.",
    "input_schema": _PRIORITIZE_SCHEMA,
}

_OAI_PRIORITIZE_TOOL = {
    "type": "function",
    "function": {
        "name": "prioritize",
        "description": "Return persona tags to prioritize for the testing focus.",
        "parameters": _PRIORITIZE_SCHEMA,
    },
}


def _tag_menu() -> str:
    return "\n".join(f"- {key}: {desc}" for key, desc in TAGS)


def _prioritize_prompt(focus: str) -> str:
    return (
        f"Testing focus: {focus or '(general usability)'}\n\n"
        f"Available tags:\n{_tag_menu()}\n\n"
        "Return the most relevant tags, most important first."
    )


def _valid_tags(tags: object) -> list[str]:
    """Keep only known tag keys, de-duplicated, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for tag in tags or []:
        if tag in TAG_KEYS and tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


async def prioritize_with_anthropic(focus: str, config: dict) -> list[str]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=config["api_key"])
    model = config.get("model") or "claude-opus-4-8"
    msg = await client.messages.create(
        model=model,
        max_tokens=512,
        system=_PRIORITIZE_SYSTEM,
        tools=[_ANTHROPIC_PRIORITIZE_TOOL],
        tool_choice={"type": "tool", "name": "prioritize"},
        messages=[{"role": "user", "content": _prioritize_prompt(focus)}],
    )
    for block in msg.content:
        if getattr(block, "type", "") == "tool_use":
            return _valid_tags(block.input.get("tags", []))
    return []


async def prioritize_with_openai(focus: str, config: dict) -> list[str]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("base_url") or None,
    )
    model = config.get("model") or "gpt-4o"
    resp = await client.chat.completions.create(
        model=model,
        max_tokens=512,
        messages=[
            {"role": "system", "content": _PRIORITIZE_SYSTEM},
            {"role": "user", "content": _prioritize_prompt(focus)},
        ],
        tools=[_OAI_PRIORITIZE_TOOL],
        tool_choice={"type": "function", "function": {"name": "prioritize"}},
    )
    for call in (resp.choices[0].message.tool_calls or []):
        if call.function.name == "prioritize":
            try:
                return _valid_tags(json.loads(call.function.arguments).get("tags", []))
            except Exception:  # noqa: BLE001
                continue
    return []


async def prioritize_with_ollama(focus: str, config: dict) -> list[str]:
    from ollama import AsyncClient

    client = AsyncClient(
        host=config.get("base_url") or "http://localhost:11434",
        timeout=120.0,
    )
    model = config.get("model") or "llama3.1"
    resp = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _PRIORITIZE_SYSTEM},
            {"role": "user", "content": _prioritize_prompt(focus)},
        ],
        tools=[_OAI_PRIORITIZE_TOOL],
    )
    for call in (getattr(resp.message, "tool_calls", None) or []):
        if getattr(call.function, "name", "") == "prioritize":
            args = call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            try:
                return _valid_tags(args.get("tags", []))
            except Exception:  # noqa: BLE001
                continue
    return []


# ── Full persona generation ("create new persona" flow) ────────────────────────

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
