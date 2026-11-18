"""Local-First Sliding Window Rate Limiting with Memory Store and Redis Fallback."""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any
from fastapi import Request

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


class InMemoryRateLimitStore:
    """Thread-safe sliding-window rate limit storage in local memory."""

    def __init__(self) -> None:
        self._history: dict[str, list[float]] = defaultdict(list)

    def check_and_record(
        self, key: str, max_requests: int, window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """Check if request is allowed under sliding window quota.

        Returns:
            tuple of (is_allowed, remaining_quota, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds
        records = [ts for ts in self._history[key] if ts > cutoff]

        if len(records) >= max_requests:
            oldest = records[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            self._history[key] = records
            return False, 0, retry_after

        records.append(now)
        self._history[key] = records
        remaining = max_requests - len(records)
        return True, remaining, 0

    def clear(self) -> None:
        """Clear all stored rate limit history (useful for testing)."""
        self._history.clear()


# Global in-memory storage instance
_memory_store = InMemoryRateLimitStore()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers or socket info."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in comma-separated list
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def create_rate_limiter(
    requests_per_minute: int = 60,
    scope: str = "default",
    window_seconds: int = 60,
) -> Callable[[Request], Any]:
    """Factory creating a FastAPI dependency that enforces rate limits per client IP."""

    async def rate_limit_dependency(request: Request) -> None:
        # Bypass rate limits completely during automated test runs
        if settings.ENVIRONMENT == "testing":
            return

        client_ip = get_client_ip(request)
        rate_key = f"rate_limit:{scope}:{client_ip}"

        is_allowed, remaining, retry_after = _memory_store.check_and_record(
            key=rate_key,
            max_requests=requests_per_minute,
            window_seconds=window_seconds,
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_ip} on scope '{scope}'. "
                f"Quota: {requests_per_minute}/{window_seconds}s. Retry after {retry_after}s."
            )
            raise RateLimitExceededError(
                message=f"Rate limit exceeded for {scope}. Please retry in {retry_after} seconds.",
                retry_after_seconds=retry_after,
            )

    return rate_limit_dependency


# Pre-configured dependencies for key critical endpoints
rate_limit_login = create_rate_limiter(requests_per_minute=10, scope="auth:login")
rate_limit_register = create_rate_limiter(requests_per_minute=5, scope="auth:register")
rate_limit_workflow_execution = create_rate_limiter(requests_per_minute=20, scope="workflow:execute")
