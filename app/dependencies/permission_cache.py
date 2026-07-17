"""
Permission Cache dependencies.

Provides FastAPI dependencies for the RBAC repository and permission cache service.
"""

import redis
from fastapi.params import Depends

from app.services.permision_cache_service import PermissionCacheService
from app.core.redis import get_redis
from app.repositories.rbac_repository import RbacRepository


def get_rbac_repo():
    """
    Provide an instance of the RbacRepository.
    """
    return RbacRepository()


def get_permission_cache_service(
    redis_client: redis.Redis = Depends(get_redis),
    rbac_repo: RbacRepository = Depends(get_rbac_repo),
):
    """
    Provide an instance of the PermissionCacheService.

    Args:
        redis_client (redis.Redis): The Redis client dependency.
        rbac_repo (RbacRepository): The RBAC repository dependency.

    Returns:
        PermissionCacheService: The instantiated service.
    """
    return PermissionCacheService(redis_client=redis_client, rbac_repository=rbac_repo)
