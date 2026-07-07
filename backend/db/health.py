import httpx
import redis.asyncio as redis
import logging
from backend.db.pool import db_pool
from backend.config import settings

logger = logging.getLogger(__name__)

async def check_postgres() -> bool:
    try:
        pool = db_pool.get_pool()
        if not pool:
            return False
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT 1")
            return val == 1
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        return False

async def check_redis() -> bool:
    try:
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            socket_connect_timeout=2
        )
        ping_ok = await r.ping()
        await r.aclose()
        return ping_ok
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

async def check_mlflow() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # MLflow server health or simple request to root
            resp = await client.get(f"{settings.mlflow_tracking_uri}/health")
            if resp.status_code == 200:
                return True
            # fallback check standard endpoint if /health not implemented on some older mlflow server
            resp = await client.get(f"{settings.mlflow_tracking_uri}/")
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"MLflow health check failed: {e}")
        return False
