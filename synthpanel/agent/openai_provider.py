"""OpenAI provider: decides the next Action via function calling.

Uses the official `openai` async client. `base_url` may point at any
OpenAI-compatible endpoint. Imported lazily so module import stays cheap.
"""

from __future__ import annotations

import json

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.prompts import SYSTEM_TEMPLATE, render_user_turn

_ACT_TOOL = {
    "type": "function",
    "function": {
        "name": "act",
        "description": "Choose exactly one next action as the persona.",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": [a.value for a in ActionType]},
                "target": {
                    "type": "string",
                    "description": 'Accessibility ref like: button "Sign in".',
                },
                "value": {"type": "string", "description": "Text to type, URL, note/bug body, etc."},
                "rationale": {"type": "string"},
            },
            "required": ["type"],
        },
    },
}


class OpenAIProvider:
    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url or None)
        self._model = model
        self.usage: dict[str, int] = {"input": 0, "output": 0}

    @property
    def model(self) -> str:
        return self._model

    def _record_usage(self, resp: object) -> None:
        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.usage["input"] += int(getattr(usage, "prompt_tokens", 0) or 0)
            self.usage["output"] += int(getattr(usage, "completion_tokens", 0) or 0)

    async def decide(self, turn: Turn) -> Action:
        content: list[dict] = [{"type": "text", "text": render_user_turn(turn)}]
        if turn.observation.screenshot_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{turn.observation.screenshot_b64}"
                    },
                }
            )
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_TEMPLATE},
                {"role": "user", "content": content},
            ],
            tools=[_ACT_TOOL],
            tool_choice={"type": "function", "function": {"name": "act"}},
        )
        self._record_usage(resp)
        for call in resp.choices[0].message.tool_calls or []:
            try:
                return Action.model_validate(json.loads(call.function.arguments))
            except Exception:  # noqa: BLE001 - skip malformed call, try the next
                continue
        return Action(type=ActionType.GIVE_UP, rationale="No tool call returned by model.")


async def list_openai_models(config: dict) -> tuple[bool, list[str] | str]:
    api_key = (config or {}).get("api_key")
    base_url = (config or {}).get("base_url") or None
    if not api_key and not base_url:
        return False, "API key is required"
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        page = await client.models.list()
        # Prefer chat-capable models; fall back to all if the heuristic empties it.
        ids = sorted(m.id for m in page.data)
        chat = [i for i in ids if i.startswith(("gpt", "o1", "o3", "o4", "chatgpt"))]
        return True, chat or ids
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


async def test_openai_connection(config: dict) -> tuple[bool, str]:
    api_key = (config or {}).get("api_key")
    base_url = (config or {}).get("base_url") or None
    if not api_key and not base_url:
        return False, "API key is required"
    model = (config or {}).get("model") or "gpt-4o"
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        await client.chat.completions.create(
            model=model,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, f"Connected ({model})"
    except Exception as exc:  # noqa: BLE001 - report any failure to the UI
        return False, f"{type(exc).__name__}: {exc}"
