"""
Permission cache service.

Handles fetching and caching of RBAC permissions using Redis to optimize database queries.
"""

import json
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.rbac_repository import RbacRepository
from app.core.config import get_settings

settings = get_settings()


class PermissionCacheService:
    """
    Service to manage caching and invalidation of user permissions in Redis.
    """

    def __init__(self, redis_client: Redis, rbac_repository: RbacRepository):
        """
        Initialize the PermissionCacheService.

        Args:
            redis_client (Redis): The Redis client instance.
            rbac_repository (RbacRepository): The RBAC repository instance.
        """
        self.redis = redis_client
        self.rbac_repository = rbac_repository

    def _key(self, user_id: int) -> str:
        """
        Generate the Redis cache key for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The formatted cache key.
        """
        return f"perms:user:{user_id}"

    async def get_user_permission(
        self, db: AsyncSession, user_id: int, organization_id: int
    ):
        """
        Retrieve a user's permissions, checking the Redis cache first before querying the DB.

        Args:
            db (AsyncSession): The database session.
            user_id (int): The ID of the user.
            organization_id (int): The ID of the organization.

        Returns:
            set: A set of permission code strings.
        """

        key = self._key(user_id)
        cached = await self.redis.get(key)

        if cached is not None:
            return set(json.loads(cached))

        print("*" * 100)
        print(cached)

        permissions = await self.rbac_repository.get_user_permissions(
            db, user_id, organization_id
        )
        await self.redis.set(
            key, json.dumps(list(permissions)), ex=settings.PERMISSION_CACHE_TTL
        )
        return set(permissions)

    async def invalidate_user(self, user_id: int) -> None:
        """Call on role reassignment, deactivation, org removal, etc."""
        await self.redis.delete(self._key(user_id))

    async def invalidate_users(self, user_ids: list[int]) -> None:
        """Bulk invalidation — e.g. when a role's permission set is edited."""
        if not user_ids:
            return
        keys = [self._key(uid) for uid in user_ids]
        await self.redis.delete(*keys)
