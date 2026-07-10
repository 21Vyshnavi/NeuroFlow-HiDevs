# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import redis.asyncio as redis
from fastapi import HTTPException

from backend.config import settings


async def check_backpressure_ingestion():
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password
    )
    
    try:
        # Check LLEN on ingestion queue
        queue_depth = await r.llen("queue:ingest")
        await r.aclose()
        
        if queue_depth > 100:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "ingestion_queue_full",
                    "queue_depth": queue_depth,
                    "retry_after": 30
                }
            )
        elif queue_depth > 50:
            # Let API caller know queue is degraded
            # Handled in route individually to return 202 instead of standard 200
            return {"warning": "high_queue_depth", "queue_depth": queue_depth}
            
        return {"status": "ok", "queue_depth": queue_depth}
    except HTTPException as e:
        raise e
    except Exception:
        return {"status": "ok", "queue_depth": 0}
