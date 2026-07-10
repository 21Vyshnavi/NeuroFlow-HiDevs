# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import asyncio
import logging

import redis.asyncio as redis

from backend.config import settings

logger = logging.getLogger(__name__)

TIMEOUTS = {
    "embedding": 10,
    "chat_completion": 60,
    "reranking": 15,
    "evaluation": 120,
    "file_extraction": 30,
    "url_fetch": 15
}

async def with_timeout(coro, task_type: str):
    timeout = TIMEOUTS.get(task_type, 30)
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        logger.error(f"Timeout exceeded for task_type={task_type} (limit={timeout}s)")
        # Increment timeout counter in Redis
        try:
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)
            await r.incr(f"timeouts:{task_type}")
            await r.aclose()
        except Exception:
            pass
        raise TimeoutError(f"{task_type} timed out after {timeout}s")
