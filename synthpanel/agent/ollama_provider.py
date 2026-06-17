"""Local Ollama provider: decides the next Action via tool calling.

Uses the official `ollama` async client (an optional dependency, imported lazily
so the package stays importable without it). Ollama's chat API takes OpenAI-style
function tools and returns parsed `message.tool_calls`.
"""

from __future__ import annotations

import json

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.prompts import SYSTEM_TEMPLATE, render_user_turn

_DEFAULT_HOST = "http://localhost:11434"

# OpenAI/Ollama function-tool form of the action schema (mirrors agent.actions.Action).
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


class OllamaProvider:
    def __init__(self, host: str, model: str, timeout: float = 300.0) -> None:
        from ollama import AsyncClient

        self._client = AsyncClient(host=host or _DEFAULT_HOST, timeout=timeout)
        self._model = model
        self.usage: dict[str, int] = {"input": 0, "output": 0}

    @property
    def model(self) -> str:
        return self._model

    def _record_usage(self, resp: object) -> None:
        self.usage["input"] += int(getattr(resp, "prompt_eval_count", 0) or 0)
        self.usage["output"] += int(getattr(resp, "eval_count", 0) or 0)

    async def decide(self, turn: Turn) -> Action:
        user_msg: dict = {"role": "user", "content": render_user_turn(turn)}
        if turn.observation.screenshot_b64:
            user_msg["images"] = [turn.observation.screenshot_b64]
        resp = await self._client.chat(
            model=self._model,
            messages=[{"role": "system", "content": SYSTEM_TEMPLATE}, user_msg],
            tools=[_ACT_TOOL],
        )
        self._record_usage(resp)
        for call in getattr(resp.message, "tool_calls", None) or []:
            args = call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            try:
                return Action.model_validate(args)
            except Exception:  # noqa: BLE001 - skip malformed call, try the next
                continue
        return Action(type=ActionType.GIVE_UP, rationale="No tool call returned by model.")


async def list_ollama_models(config: dict) -> tuple[bool, list[str] | str]:
    host = (config or {}).get("base_url") or _DEFAULT_HOST
    try:
        from ollama import AsyncClient

        listing = await AsyncClient(host=host).list()
        names = [m.get("model") or m.get("name") for m in (listing.get("models") or [])]
        return True, [n for n in names if n]
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


async def test_ollama_connection(config: dict) -> tuple[bool, str]:
    host = (config or {}).get("base_url") or _DEFAULT_HOST
    model = (config or {}).get("model")
    try:
        from ollama import AsyncClient

        client = AsyncClient(host=host)
        listing = await client.list()
        if model:
            names = {m.get("model") or m.get("name") for m in (listing.get("models") or [])}
            # Ollama tags often carry a ":tag"; accept a prefix match.
            if names and not any(n and n.split(":")[0] == model.split(":")[0] for n in names):
                return False, f"model '{model}' not found on {host} (run `ollama pull {model}`)"
        return True, f"Connected ({host})"
    except Exception as exc:  # noqa: BLE001 - report any failure to the UI
        return False, f"{type(exc).__name__}: {exc}"
