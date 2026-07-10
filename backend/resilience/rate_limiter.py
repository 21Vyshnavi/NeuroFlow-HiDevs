# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import time

import redis.asyncio as redis
from fastapi import HTTPException, Request

from backend.config import settings


class TokenBucketRateLimiter:
    def __init__(self, key_prefix: str, capacity: int, replenish_rate: float) -> None:
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.replenish_rate = replenish_rate

    def _get_redis(self):
        return redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)

    async def consume(self, key_id: str, tokens: int = 1) -> bool:
        r = self._get_redis()
        key = f"rpb:{self.key_prefix}:{key_id}"
        now = time.time()
        
        # Get last state
        data = await r.hmget(key, ["tokens", "last_updated"])
        current_tokens = float(data[0] or self.capacity)
        last_updated = float(data[1] or now)

        # Replenish
        elapsed = now - last_updated
        replenished = elapsed * self.replenish_rate
        new_tokens = min(self.capacity, current_tokens + replenished)

        if new_tokens >= tokens:
            new_tokens -= tokens
            await r.hset(key, mapping={"tokens": new_tokens, "last_updated": now})
            await r.aclose()
            return True
            
        await r.aclose()
        return False

# Middleware wrapper for API endpoint rate limits
async def api_rate_limiter_middleware(request: Request, limit_rpm: int = 60) -> None:
    client_ip = request.client.host
    limiter = TokenBucketRateLimiter("api_ip", capacity=limit_rpm, replenish_rate=limit_rpm/60.0)
    
    allowed = await limiter.consume(client_ip, 1)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests. Rate limit exceeded.",
            headers={"Retry-After": "60"}
        )
