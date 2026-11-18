"""Unit tests for Rate Limiting Module and InMemoryRateLimitStore."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request

from app.core.exceptions import RateLimitExceededError
from app.core.rate_limit import (
    InMemoryRateLimitStore,
    create_rate_limiter,
    get_client_ip,
)


def test_in_memory_store_allows_under_limit():
    """Verify requests within quota are allowed and quota decrements."""
    store = InMemoryRateLimitStore()
    key = "test:user:1"

    allowed1, remaining1, retry1 = store.check_and_record(key, max_requests=3, window_seconds=60)
    assert allowed1 is True
    assert remaining1 == 2
    assert retry1 == 0

    allowed2, remaining2, retry2 = store.check_and_record(key, max_requests=3, window_seconds=60)
    assert allowed2 is True
    assert remaining2 == 1
    assert retry2 == 0

    allowed3, remaining3, retry3 = store.check_and_record(key, max_requests=3, window_seconds=60)
    assert allowed3 is True
    assert remaining3 == 0
    assert retry3 == 0


def test_in_memory_store_blocks_when_quota_exceeded():
    """Verify exceeding max_requests returns allowed=False and positive retry_after."""
    store = InMemoryRateLimitStore()
    key = "test:user:blocked"

    # Consume all 2 tokens
    store.check_and_record(key, max_requests=2, window_seconds=60)
    store.check_and_record(key, max_requests=2, window_seconds=60)

    # 3rd request must be blocked
    allowed, remaining, retry_after = store.check_and_record(key, max_requests=2, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


def test_in_memory_store_window_expiration():
    """Verify timestamps older than window_seconds are pruned."""
    store = InMemoryRateLimitStore()
    key = "test:user:expired"

    # Seed an expired timestamp (70s ago)
    store._history[key] = [100.0]

    with patch("time.time", return_value=175.0):
        # 175 - 60 = 115 cutoff; 100.0 is pruned
        allowed, remaining, _ = store.check_and_record(key, max_requests=1, window_seconds=60)
        assert allowed is True
        assert remaining == 0


def test_client_ip_extraction():
    """Verify client IP extraction handles X-Forwarded-For, X-Real-IP, and client socket."""
    # 1. X-Forwarded-For
    req1 = MagicMock(spec=Request)
    req1.headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18"}
    assert get_client_ip(req1) == "203.0.113.195"

    # 2. X-Real-IP
    req2 = MagicMock(spec=Request)
    req2.headers = {"X-Real-IP": "198.51.100.42"}
    assert get_client_ip(req2) == "198.51.100.42"

    # 3. Direct client
    req3 = MagicMock(spec=Request)
    req3.headers = {}
    req3.client.host = "192.168.1.50"
    assert get_client_ip(req3) == "192.168.1.50"


@pytest.mark.asyncio
async def test_create_rate_limiter_dependency():
    """Verify rate limiter dependency raises RateLimitExceededError when exceeded in non-testing env."""
    limiter = create_rate_limiter(requests_per_minute=2, scope="test_scope", window_seconds=60)

    req = MagicMock(spec=Request)
    req.headers = {}
    req.client.host = "10.0.0.99"

    with patch("app.core.config.settings.ENVIRONMENT", "production"):
        # First 2 should pass
        await limiter(req)
        await limiter(req)

        # 3rd should raise RateLimitExceededError
        with pytest.raises(RateLimitExceededError) as exc_info:
            await limiter(req)
        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after_seconds > 0


@pytest.mark.asyncio
async def test_rate_limiter_bypasses_in_testing_env():
    """Verify that in testing environment, rate limits are bypassed completely."""
    limiter = create_rate_limiter(requests_per_minute=1, scope="test_testing", window_seconds=60)

    req = MagicMock(spec=Request)
    req.headers = {}
    req.client.host = "10.0.0.1"

    with patch("app.core.config.settings.ENVIRONMENT", "testing"):
        # Should never raise even after multiple calls
        for _ in range(10):
            await limiter(req)
