"""
Rate limiting dependencies.

Provides FastAPI dependencies for rate limiting API endpoints using Redis.
"""

from fastapi import Depends, HTTPException, Request, status
import redis.asyncio as redis
from app.core.redis import get_redis


class RateLimiter:
    """
    Dependency class to enforce rate limits on FastAPI routes.
    """

    def __init__(self, seconds: int, times: int, scope: str | None = None):
        """
        Initialize the rate limiter.

        Args:
            seconds (int): The time window in seconds.
            times (int): The maximum number of allowed requests in the time window.
            scope (str | None): An optional string to scope the rate limit.
        """
        self.seconds = seconds
        self.times = times
        self.scope = scope

    async def __call__(
        self, request: Request, redis_client: redis.Redis = Depends(get_redis)
    ) -> None:
        identity = getattr(request.state, "user_id", None) or self._client_ip(request)
        bucket = self.scope or request.url.path
        key = f"ratelimit:{identity}:{bucket}"

        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, self.seconds)

        if current > self.times:
            ttl = await redis_client.ttl(key)
            retry_after = ttl if ttl > 0 else self.seconds

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    @staticmethod
    def _client_ip(request: Request) -> str:
        """
        Extract the client's IP address from the request.

        Args:
            request (Request): The incoming FastAPI request.

        Returns:
            str: The client IP address.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
