import asyncio
import json
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

_clients: list[asyncio.Queue] = []


async def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _clients.append(q)
    logger.info(f"SSE client connected. Total: {len(_clients)}")
    return q


def unsubscribe(q: asyncio.Queue):
    if q in _clients:
        _clients.remove(q)
    logger.info(f"SSE client disconnected. Total: {len(_clients)}")


async def broadcast(event: dict):
    if not _clients:
        return
    for q in _clients:
        try:
            await q.put(event)
        except Exception as e:
            logger.error(f"SSE broadcast error: {e}")


async def event_generator(q: asyncio.Queue) -> AsyncGenerator[str, None]:
    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield 'data: {"type": "ping"}\n\n'
    except asyncio.CancelledError:
        pass