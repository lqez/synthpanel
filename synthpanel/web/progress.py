"""In-process pub/sub for live run progress, consumed by the SSE endpoint.

Each run buffers its events so a subscriber that connects mid-run (or just after
it finishes) still replays the full history, then follows live updates until a
finish sentinel. Single-process, single-user — no external broker needed.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator


class RunBroker:
    def __init__(self) -> None:
        self._subs: dict[int, list[asyncio.Queue]] = {}
        self._history: dict[int, list[dict]] = {}
        self._done: set[int] = set()

    def publish(self, run_id: int, event: dict) -> None:
        self._history.setdefault(run_id, []).append(event)
        for q in self._subs.get(run_id, []):
            q.put_nowait(event)

    def finish(self, run_id: int) -> None:
        self._done.add(run_id)
        for q in self._subs.get(run_id, []):
            q.put_nowait(None)  # sentinel

    async def stream(self, run_id: int) -> AsyncIterator[dict | None]:
        """Replay buffered events, then yield live ones until done (None sentinel)."""
        q: asyncio.Queue = asyncio.Queue()
        self._subs.setdefault(run_id, []).append(q)
        try:
            for event in list(self._history.get(run_id, [])):
                yield event
            if run_id in self._done:
                yield None
                return
            while True:
                event = await q.get()
                if event is None:
                    yield None
                    return
                yield event
        finally:
            self._subs.get(run_id, []).remove(q)
