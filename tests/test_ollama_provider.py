"""Unit tests for the Ollama provider. No `ollama` package or server needed:
decide() runs against an injected fake client; the connection helper degrades
gracefully when the dependency/host is absent."""

from __future__ import annotations

import pytest

from synthpanel.agent.actions import ActionType
from synthpanel.agent.llm import Turn
from synthpanel.agent.ollama_provider import OllamaProvider
from synthpanel.agent.ollama_provider import test_ollama_connection as check_connection
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation


class _Fn:
    def __init__(self, arguments):
        self.arguments = arguments


class _Call:
    def __init__(self, arguments):
        self.function = _Fn(arguments)


class _Msg:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class _Resp:
    def __init__(self, tool_calls, prompt_eval_count=0, eval_count=0):
        self.message = _Msg(tool_calls)
        self.prompt_eval_count = prompt_eval_count
        self.eval_count = eval_count


class _Client:
    def __init__(self, resp):
        self._resp = resp
        self.calls: list[dict] = []

    async def chat(self, **kw):
        self.calls.append(kw)
        return self._resp


def _provider(tool_calls, prompt_eval_count=0, eval_count=0):
    p = object.__new__(OllamaProvider)
    p._client = _Client(_Resp(tool_calls, prompt_eval_count, eval_count))
    p._model = "llama3.1"
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
    p = _provider([_Call({"type": "click", "target": 'button "Go"', "rationale": "r"})])
    action = await p.decide(_turn())
    assert action.type is ActionType.CLICK
    assert action.target == 'button "Go"'


async def test_decide_gives_up_when_no_tool_calls():
    p = _provider([])
    action = await p.decide(_turn())
    assert action.type is ActionType.GIVE_UP


async def test_decide_accumulates_usage():
    p = _provider([_Call({"type": "done"})], prompt_eval_count=80, eval_count=12)
    await p.decide(_turn())
    await p.decide(_turn())
    assert p.usage == {"input": 160, "output": 24}


async def test_decide_attaches_image_in_vision_mode():
    p = _provider([_Call({"type": "done"})])
    await p.decide(_turn(Observation(url="u", screenshot_b64="QUJD")))
    user_msg = p._client.calls[0]["messages"][1]
    assert user_msg.get("images") == ["QUJD"]


async def test_connection_reports_failure_gracefully():
    # No `ollama` installed / no server -> graceful (False, message), never raises.
    ok, msg = await check_connection({"base_url": "http://localhost:11434", "model": "llama3.1"})
    assert ok is False
    assert isinstance(msg, str) and msg
