"""
Redis client module.

Provides initialization, shutdown, and access to the Redis connection pool.
"""

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()
redis_client: redis.Redis | None = None


async def init_redis() -> None:
    """
    Initialize the global Redis connection using settings.
    """
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await redis_client.ping()


async def close_redis() -> None:
    """
    Close the global Redis connection gracefully.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> redis.Redis:
    """
    Retrieve the initialized Redis client.

    Returns:
        redis.Redis: The active Redis connection.

    Raises:
        RuntimeError: If the Redis client has not been initialized.
    """
    if redis_client is None:
        raise RuntimeError(
            "Redis client not initialized. Did the app startup lifespan run?"
        )
    return redis_client
