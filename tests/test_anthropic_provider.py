"""Unit tests for the real Anthropic provider's parsing and connection paths.

The `anthropic` package isn't required: we bypass __init__ and inject a fake
async client, so only our tool-use -> Action mapping is under test. The
connection helper's no-key and failure paths are covered directly.
"""

from __future__ import annotations

import pytest

from synthpanel.agent.actions import ActionType
from synthpanel.agent.anthropic_provider import AnthropicProvider
from synthpanel.agent.anthropic_provider import test_anthropic_connection as check_connection
from synthpanel.agent.llm import Turn
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation


class _Block:
    def __init__(self, type_: str, **attrs):
        self.type = type_
        for k, v in attrs.items():
            setattr(self, k, v)


class _Usage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _Messages:
    def __init__(self, content, usage=None):
        self._content = content
        self._usage = usage
        self.calls: list[dict] = []

    async def create(self, **kw):
        self.calls.append(kw)
        return type("Msg", (), {"content": self._content, "usage": self._usage})()


def _provider(content, usage=None):
    p = object.__new__(AnthropicProvider)
    p._client = type("C", (), {"messages": _Messages(content, usage)})()
    p._model = "claude-test"
    p.usage = {"input": 0, "output": 0}
    return p


def _turn(observation=None):
    return Turn(
        persona=Persona(name="x", intent=Intent(goal="g")),
        observation=observation or Observation(url="https://app.test"),
        history=[],
        step_idx=0,
    )


async def test_decide_parses_tool_use_into_action():
    p = _provider([_Block("tool_use", input={"type": "click", "target": 'button "Go"', "rationale": "r"})])
    action = await p.decide(_turn())
    assert action.type is ActionType.CLICK
    assert action.target == 'button "Go"'
    assert action.rationale == "r"


async def test_decide_gives_up_when_no_tool_use():
    p = _provider([_Block("text", text="just chatting")])
    action = await p.decide(_turn())
    assert action.type is ActionType.GIVE_UP


async def test_decide_accumulates_token_usage():
    p = _provider([_Block("tool_use", input={"type": "done"})], usage=_Usage(100, 20))
    await p.decide(_turn())
    await p.decide(_turn())
    assert p.usage == {"input": 200, "output": 40}


async def test_decide_attaches_screenshot_in_vision_mode():
    p = _provider([_Block("tool_use", input={"type": "done"})])
    await p.decide(_turn(Observation(url="u", screenshot_b64="QUJD")))
    content = p._client.messages.calls[0]["messages"][0]["content"]
    assert any(block.get("type") == "image" for block in content)


async def test_connection_requires_api_key():
    ok, msg = await check_connection({})
    assert ok is False
    assert "API key" in msg


async def test_connection_reports_failure_gracefully():
    # No `anthropic` installed (or no network) -> graceful (False, message),
    # never an unhandled exception.
    ok, msg = await check_connection({"api_key": "bad-key"})
    assert ok is False
    assert isinstance(msg, str) and msg
