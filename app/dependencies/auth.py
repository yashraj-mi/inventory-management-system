"""
Dependency injection module for auth.py.

Provides FastAPI dependencies for auth components.
"""

from typing import List
from fastapi import Depends, status

from app.constants.user_enum import UserRole
from app.core.exceptions import AppException
from app.constants.auth_enum import AuthMessages
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService
from app.dependencies.organization import get_organization_repo
from app.repositories.organization_repository import OrganizationRepository
from app.core.security import get_current_user


def get_auth_repo() -> AuthRepository:
    """
    Provide a auth repository instance.

    Returns:
        Repository instance for database operations.
    """
    return AuthRepository()


def get_auth_service(
    auth_repo: AuthRepository = Depends(get_auth_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
) -> AuthService:
    """
    Provide a auth service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return AuthService(auth_repo=auth_repo, org_repo=org_repo)


class RoleChecker:
    """
    Dependency class to enforce role-based access control (RBAC).

    Args:
        allowed_roles (List[UserRole]): A list of roles permitted to access the route.
    """

    def __init__(self, allowed_roles: List[UserRole]):
        """
        Initialize the RoleChecker with a list of permitted roles.

        Args:
            allowed_roles (List[UserRole]): The list of roles that have access.
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user=Depends(get_current_user)):
        """
        Validates the current user's role against the allowed roles.

        Args:
            current_user (dict): The decoded JWT payload of the authenticated user.

        Returns:
            dict: The current user payload if authorized.

        Raises:
            AppException: If the user's role is not in the allowed list (403).
        """
        role = current_user.get("role")
        if role not in [r.value for r in self.allowed_roles]:
            raise AppException(
                message=AuthMessages.RESOURCE_ACCESS,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return current_user


# Pre-built role policy constants for use as FastAPI dependencies
ALLOW_SUPER_ADMIN = RoleChecker([UserRole.SUPER_ADMIN])
ALLOW_ORG_ADMIN = RoleChecker([UserRole.ORG_ADMIN])
ALLOW_ADMIN_OR_MANAGER = RoleChecker([UserRole.ORG_ADMIN, UserRole.WAREHOUSE_MANAGER])
ALLOW_COMMON_ORG = RoleChecker(
    [UserRole.ORG_ADMIN, UserRole.WAREHOUSE_MANAGER, UserRole.WAREHOUSE_STAFF]
)
ALLOW_SUPER_ADMIN_OR_ORG_ADMIN = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])


def verify_tenant_access(current_user: dict, target_org_id: int) -> None:
    """
    Ensures the current user belongs to the target organization, unless they are a Super Admin.

    Args:
        current_user (dict): The decoded JWT payload of the authenticated user.
        target_org_id (int): The organization ID of the requested resource.

    Raises:
        AppException: If the user attempts to access a different organization's data.
    """
    user_role = current_user.get("role")
    user_org_id = current_user.get("org_id")

    if user_role != UserRole.SUPER_ADMIN.value and user_org_id != target_org_id:
        raise AppException(
            message=AuthMessages.NO_PERMISSION,
            status_code=status.HTTP_403_FORBIDDEN,
        )
