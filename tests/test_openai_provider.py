"""Unit tests for the OpenAI provider, using an injected fake client."""

from __future__ import annotations

import json

import pytest

from synthpanel.agent.actions import ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.openai_provider import OpenAIProvider
from synthpanel.agent.openai_provider import test_openai_connection as check_connection
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation


class _Fn:
    def __init__(self, arguments):
        self.arguments = arguments


class _Call:
    def __init__(self, arguments):
        self.function = _Fn(json.dumps(arguments))


class _Msg:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class _Choice:
    def __init__(self, tool_calls):
        self.message = _Msg(tool_calls)


class _Usage:
    def __init__(self, prompt_tokens, completion_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _Resp:
    def __init__(self, tool_calls, usage=None):
        self.choices = [_Choice(tool_calls)]
        self.usage = usage


class _Completions:
    def __init__(self, resp):
        self._resp = resp
        self.calls: list[dict] = []

    async def create(self, **kw):
        self.calls.append(kw)
        return self._resp


def _provider(tool_calls, usage=None):
    p = object.__new__(OpenAIProvider)
    completions = _Completions(_Resp(tool_calls, usage))
    p._client = type("C", (), {"chat": type("Ch", (), {"completions": completions})()})()
    p._model = "gpt-4o"
    p.usage = {"input": 0, "output": 0}
    return p


def _turn(observation=None):
    return Turn(
        persona=Persona(name="x", intent=Intent(goal="g")),
        observation=observation or Observation(url="https://app.test"),
        history=[],
        step_idx=0,
    )


async def test_decide_parses_tool_call_into_action():
    p = _provider([_Call({"type": "type", "target": 'textbox "Email"', "value": "a@b.com"})])
    action = await p.decide(_turn())
    assert action.type is ActionType.TYPE
    assert action.value == "a@b.com"


async def test_decide_gives_up_when_no_tool_calls():
    p = _provider([])
    assert (await p.decide(_turn())).type is ActionType.GIVE_UP


async def test_decide_accumulates_usage():
    p = _provider([_Call({"type": "done"})], usage=_Usage(90, 15))
    await p.decide(_turn())
    await p.decide(_turn())
    assert p.usage == {"input": 180, "output": 30}


async def test_decide_attaches_image_in_vision_mode():
    p = _provider([_Call({"type": "done"})])
    await p.decide(_turn(Observation(url="u", screenshot_b64="QUJD")))
    content = p._client.chat.completions.calls[0]["messages"][1]["content"]
    assert any(part.get("type") == "image_url" for part in content)


async def test_connection_requires_api_key():
    ok, msg = await check_connection({})
    assert ok is False
    assert "API key" in msg


async def test_connection_reports_failure_gracefully():
    ok, msg = await check_connection({"api_key": "bad-key"})
    assert ok is False
    assert isinstance(msg, str) and msg
