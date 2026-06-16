"""Real Anthropic provider: decides the next Action via tool-use.

The `anthropic` package and network are only touched at call time, so importing
this module is cheap and safe in environments without the dependency or a key.
"""

from __future__ import annotations

from synthpanel.agent.actions import Action, ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.prompts import SYSTEM_TEMPLATE, render_user_turn

# Tool schema mirrors agent.actions.Action so the model returns a valid Action.
_ACT_TOOL = {
    "name": "act",
    "description": "Choose exactly one next action as the persona.",
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": [a.value for a in ActionType]},
            "target": {
                "type": "string",
                "description": 'Accessibility ref like: button "Sign in".',
            },
            "value": {
                "type": "string",
                "description": "Text to type, URL, note/bug body, etc.",
            },
            "rationale": {"type": "string"},
        },
        "required": ["type"],
    },
}


class AnthropicProvider:
    def __init__(self, api_key: str, model: str) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def decide(self, turn: Turn) -> Action:
        content: list[dict] = [{"type": "text", "text": render_user_turn(turn)}]
        if turn.observation.screenshot_b64:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": turn.observation.screenshot_b64,
                    },
                }
            )
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_TEMPLATE,
            tools=[_ACT_TOOL],
            tool_choice={"type": "tool", "name": "act"},
            messages=[{"role": "user", "content": content}],
        )
        for block in msg.content:
            if getattr(block, "type", "") == "tool_use":
                return Action.model_validate(block.input)
        return Action(type=ActionType.GIVE_UP, rationale="No action returned by model.")


async def test_anthropic_connection(config: dict) -> tuple[bool, str]:
    api_key = (config or {}).get("api_key")
    if not api_key:
        return False, "API key is required"
    model = config.get("model") or "claude-opus-4-8"
    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
        await client.messages.create(
            model=model,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, f"Connected ({model})"
    except Exception as exc:  # noqa: BLE001 - report any failure to the UI
        return False, f"{type(exc).__name__}: {exc}"
