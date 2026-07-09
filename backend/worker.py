import os
import json
import logging
import redis.asyncio as redis
from backend.db.pool import db_pool
from pipelines.ingestion.pipeline import process_document_job
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

async def worker_loop():
    logger.info("Initializing Worker and Connecting Database Pool...")
    await db_pool.connect()

    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password
    )

    logger.info("Worker polling queue:ingest...")
    while True:
        try:
            # Update queue depth metric
            try:
                q_len = await r.llen("queue:ingest")
                from backend.monitoring.metrics import queue_depth
                queue_depth.set(q_len)
            except Exception:
                pass

            # Block pop job from redis queue
            job = await r.brpop("queue:ingest", timeout=5)
            if job:
                # job is a tuple (key, value)
                payload = json.loads(job[1].decode('utf-8'))
                logger.info(f"Received ingestion task: {payload}")
                
                await process_document_job(
                    document_id=payload["document_id"],
                    file_path=payload.get("file_path"),
                    source_type=payload["source_type"],
                    url=payload.get("url")
                )
        except Exception as e:
            logger.error(f"Worker Loop Exception: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    import asyncio
    asyncio.run(worker_loop())
