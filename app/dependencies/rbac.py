"""
RBAC Dependencies.

Provides FastAPI dependency generators for enforcing required permissions and roles.
"""

from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app.core.database import get_db
from app.dependencies.permission_cache import get_permission_cache_service
from app.services.permision_cache_service import PermissionCacheService
from app.repositories.rbac_repository import RbacRepository


def require_permission(permission_code: str):
    """
    Dependency generator that enforces a specific permission requirement.

    Args:
        permission_code (str): The code of the required permission.

    Returns:
        Callable: A FastAPI dependency that performs the authorization check.
    """

    async def checker(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
        permission_cache: PermissionCacheService = Depends(
            get_permission_cache_service
        ),
    ):
        """
        Inner dependency function that checks if the current user possesses the required permission.
        """
        # rbac_repo=RbacRepository()
        # permissions = await rbac_repo.get_user_permissions(
        #     db, current_user.id, current_user.organization_id
        # )
        permissions = await permission_cache.get_user_permission(
            db, current_user.id, current_user.organization_id
        )
        if permission_code not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission_code}",
            )
        return current_user

    return checker


def require_role(required_role: str):
    """
    Dependency generator that enforces a specific system-wide role requirement.

    Args:
        required_role (str): The name of the required role (e.g., 'SUPER_ADMIN').

    Returns:
        Callable: A FastAPI dependency that performs the authorization check.
    """

    async def checker(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ):
        """
        Inner dependency function that checks if the current user holds the required role.
        """
        rbac_repo = RbacRepository()
        if required_role == "SUPER_ADMIN":
            has_role = await rbac_repo.has_platform_role(
                db, current_user.id, required_role
            )
            if not has_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role: {required_role}",
                )
        return current_user

    return checker
