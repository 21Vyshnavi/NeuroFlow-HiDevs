# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
"""
GET /evaluations/stream — SSE endpoint for real-time evaluation feed.
Subscribes to Redis pub/sub channel 'evaluations:new' and forwards
each new evaluation as a Server-Sent Event to connected clients.
"""
import asyncio
import logging

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from backend.config import settings
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluations", tags=["evaluations"], dependencies=[Depends(get_current_user)])


async def _evaluation_event_generator():
    """Subscribe to Redis pub/sub and yield evaluation events."""
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
    )
    pubsub = r.pubsub()
    await pubsub.subscribe("evaluations:new")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                yield {"event": "evaluation", "data": data}
            else:
                # Send keepalive comment every second to detect disconnects
                yield {"comment": "keepalive"}
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe("evaluations:new")
        await pubsub.aclose()
        await r.aclose()


@router.get("/stream")
async def evaluation_stream():
    """SSE endpoint that streams evaluation results in real-time.

    Each event contains a JSON payload with evaluation scores,
    pipeline name, query text, and associated metadata.
    """
    return EventSourceResponse(_evaluation_event_generator())


@router.get("")
async def list_evaluations(
    pipeline: str | None = None,
    metric: str | None = None,
    threshold: float | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List recent evaluations with optional filters."""
    from backend.db.pool import db_pool

    conditions = []
    params = []
    idx = 1

    if pipeline:
        conditions.append(f"pipeline_name = ${idx}")
        params.append(pipeline)
        idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT id, run_id, pipeline_name, query_text,
               faithfulness, relevance, coherence, groundedness,
               overall_score, created_at
        FROM evaluations
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${idx} OFFSET ${idx + 1}
    """
    params.extend([limit, offset])

    pool = db_pool.get_pool()
    if not pool:
        return {"evaluations": [], "total": 0}

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    results = []
    for row in rows:
        record = dict(row)
        # Apply metric threshold filter in application layer
        if metric and threshold is not None:
            score = record.get(metric)
            if score is not None and score >= threshold:
                continue
        record["created_at"] = record["created_at"].isoformat()
        results.append(record)

    return {"evaluations": results, "total": len(results)}
