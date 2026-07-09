import time
import logging
import redis.asyncio as redis
from backend.config import settings

logger = logging.getLogger(__name__)

class CircuitOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60, half_open_max_calls: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

    def _get_redis(self):
        return redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)

    async def __aenter__(self):
        r = self._get_redis()
        # Fetch status
        state = (await r.get(f"circuit:{self.name}:state") or b"CLOSED").decode("utf-8")
        
        if state == "OPEN":
            opened_at = float(await r.get(f"circuit:{self.name}:opened_at") or 0.0)
            if time.time() - opened_at > self.recovery_timeout:
                # Transition to HALF_OPEN
                await r.set(f"circuit:{self.name}:state", "HALF_OPEN")
                await r.set(f"circuit:{self.name}:half_open_calls", 0)
                state = "HALF_OPEN"
                logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")
            else:
                await r.aclose()
                raise CircuitOpenError(f"Circuit {self.name} is open.")

        if state == "HALF_OPEN":
            calls = await r.incr(f"circuit:{self.name}:half_open_calls")
            if calls > self.half_open_max_calls:
                await r.aclose()
                raise CircuitOpenError(f"Circuit {self.name} is open (half-open limit exceeded).")

        await r.aclose()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        r = self._get_redis()
        state = (await r.get(f"circuit:{self.name}:state") or b"CLOSED").decode("utf-8")

        if exc_type is not None:
            # Call failed
            failures = await r.incr(f"circuit:{self.name}:failure_count")
            if failures >= self.failure_threshold or state == "HALF_OPEN":
                was_closed = state != "OPEN"
                await r.set(f"circuit:{self.name}:state", "OPEN")
                await r.set(f"circuit:{self.name}:opened_at", time.time())
                logger.error(f"Circuit breaker {self.name} tripped to OPEN.")
                
                try:
                    from backend.monitoring.metrics import circuit_breaker_trips, active_circuit_breakers_open
                    if was_closed:
                        circuit_breaker_trips.labels(provider=self.name).inc()
                        active_circuit_breakers_open.inc()
                except ImportError:
                    pass
        else:
            # Call succeeded
            if state == "HALF_OPEN":
                # Success in half open resets circuit to closed
                await r.set(f"circuit:{self.name}:state", "CLOSED")
                await r.set(f"circuit:{self.name}:failure_count", 0)
                logger.info(f"Circuit breaker {self.name} successfully CLOSED.")
                
                try:
                    from backend.monitoring.metrics import active_circuit_breakers_open
                    active_circuit_breakers_open.dec()
                except ImportError:
                    pass
            elif state == "CLOSED":
                await r.set(f"circuit:{self.name}:failure_count", 0)

        await r.aclose()
        return False  # Do not suppress exception
