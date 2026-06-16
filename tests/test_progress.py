import asyncio

import pytest

from synthpanel.web.progress import RunBroker

pytestmark = pytest.mark.asyncio


async def test_replays_history_then_finishes():
    broker = RunBroker()
    broker.publish(1, {"kind": "start"})
    broker.publish(1, {"kind": "finish"})
    broker.finish(1)

    seen = [ev async for ev in broker.stream(1)]
    # Two events then the None sentinel.
    assert seen[0]["kind"] == "start"
    assert seen[1]["kind"] == "finish"
    assert seen[-1] is None


async def test_live_events_delivered_to_subscriber():
    broker = RunBroker()

    async def consume():
        out = []
        async for ev in broker.stream(7):
            out.append(ev)
            if ev is None:
                break
        return out

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)  # let the subscriber attach
    broker.publish(7, {"kind": "start", "persona": "A"})
    broker.finish(7)
    out = await asyncio.wait_for(task, timeout=1)
    assert out[0]["persona"] == "A"
    assert out[-1] is None
