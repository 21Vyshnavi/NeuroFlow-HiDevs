"""
Unit tests for the CircuitBreaker state machine.
Uses an in-memory Redis fake so no live Redis is required.
"""
import pytest
from unittest.mock import MagicMock, patch

import backend.resilience.circuit_breaker as cb_module
from backend.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError


# ---------------------------------------------------------------------------
# In-memory Redis fake
# ---------------------------------------------------------------------------

def _make_fake_redis():
    """Return a MagicMock whose get/set/incr/aclose are plain async functions
    backed by an in-memory dict."""
    store: dict = {}

    async def fake_get(key):
        return store.get(key)

    async def fake_set(key, value, *a, **kw):
        store[key] = str(value).encode() if not isinstance(value, bytes) else value

    async def fake_incr(key):
        current = int(store.get(key, b"0"))
        store[key] = str(current + 1).encode()
        return current + 1

    async def fake_aclose():
        pass

    fake_r = MagicMock()
    fake_r.get = fake_get
    fake_r.set = fake_set
    fake_r.incr = fake_incr
    fake_r.aclose = fake_aclose
    fake_r._store = store  # expose for assertions
    return fake_r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cb_starts_closed():
    """A new circuit breaker should be in CLOSED state."""
    fake_r = _make_fake_redis()
    with patch.object(cb_module, "redis") as mock_redis:
        mock_redis.Redis.return_value = fake_r
        cb = CircuitBreaker(name="test-closed", failure_threshold=3, recovery_timeout=60)
        # Entering the CB should succeed without raising
        async with cb:
            pass  # no exception → success path


@pytest.mark.asyncio
async def test_cb_opens_after_threshold():
    """Circuit should open after failure_threshold consecutive failures."""
    fake_r = _make_fake_redis()
    with patch.object(cb_module, "redis") as mock_redis:
        mock_redis.Redis.return_value = fake_r
        cb = CircuitBreaker(name="test-open", failure_threshold=2, recovery_timeout=60)

        for _ in range(3):
            try:
                async with cb:
                    raise RuntimeError("boom")
            except (RuntimeError, CircuitOpenError):
                pass

        with pytest.raises(CircuitOpenError):
            async with cb:
                pass


@pytest.mark.asyncio
async def test_cb_open_error_message():
    """CircuitOpenError should contain the circuit name."""
    fake_r = _make_fake_redis()
    with patch.object(cb_module, "redis") as mock_redis:
        mock_redis.Redis.return_value = fake_r
        cb = CircuitBreaker(name="named-breaker", failure_threshold=1, recovery_timeout=60)

        try:
            async with cb:
                raise RuntimeError("fail")
        except RuntimeError:
            pass

        with pytest.raises(CircuitOpenError, match="named-breaker"):
            async with cb:
                pass


@pytest.mark.asyncio
async def test_cb_success_resets_failures():
    """A successful call should reset the failure counter."""
    fake_r = _make_fake_redis()
    with patch.object(cb_module, "redis") as mock_redis:
        mock_redis.Redis.return_value = fake_r
        cb = CircuitBreaker(name="test-reset", failure_threshold=3, recovery_timeout=60)

        # 2 failures (below threshold of 3)
        for _ in range(2):
            try:
                async with cb:
                    raise RuntimeError("fail")
            except RuntimeError:
                pass

        # 1 success resets the counter
        async with cb:
            pass

        # 2 more failures should NOT trip (counter was reset)
        for _ in range(2):
            try:
                async with cb:
                    raise RuntimeError("fail")
            except RuntimeError:
                pass

        # Should still be usable (2 < 3)
        async with cb:
            pass  # no CircuitOpenError


@pytest.mark.asyncio
async def test_cb_does_not_suppress_exceptions():
    """The circuit breaker should not suppress the original exception."""
    fake_r = _make_fake_redis()
    with patch.object(cb_module, "redis") as mock_redis:
        mock_redis.Redis.return_value = fake_r
        cb = CircuitBreaker(name="test-propagate", failure_threshold=5, recovery_timeout=60)

        with pytest.raises(ValueError, match="custom error"):
            async with cb:
                raise ValueError("custom error")


@pytest.mark.asyncio
async def test_cb_half_open_transitions():
    """After recovery_timeout, the circuit should transition to HALF_OPEN."""
    import time
    fake_r = _make_fake_redis()
    with patch.object(cb_module, "redis") as mock_redis:
        mock_redis.Redis.return_value = fake_r
        cb = CircuitBreaker(name="test-half", failure_threshold=1, recovery_timeout=1)

        # Trip the breaker
        try:
            async with cb:
                raise RuntimeError("fail")
        except RuntimeError:
            pass

        # Verify it is now open
        with pytest.raises(CircuitOpenError):
            async with cb:
                pass

        # Fast-forward past recovery_timeout by patching opened_at
        opened_key = "circuit:test-half:opened_at"
        fake_r._store[opened_key] = str(time.time() - 10).encode()

        # Should now be HALF_OPEN and allow a probe call
        async with cb:
            pass  # success → should transition back to CLOSED
