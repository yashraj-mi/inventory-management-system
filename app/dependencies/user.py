"""
Dependency injection module for user.py.

Provides FastAPI dependencies for user components.
"""

from fastapi import Depends

from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.user_service import UserService
from app.dependencies.organization import get_organization_repo
from app.dependencies.permission_cache import get_rbac_repo
from app.repositories.rbac_repository import RbacRepository


def get_user_repo() -> UserRepository:
    """
    Provide a user repository instance.

    Returns:
        Repository instance for database operations.
    """
    return UserRepository()


from app.repositories.warehouse_repository import WarehouseRepository
from app.dependencies.warehouse import get_warehouse_repo


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
    warehouse_repo: WarehouseRepository = Depends(get_warehouse_repo),
    rbac_repo: RbacRepository = Depends(get_rbac_repo),
) -> UserService:
    """
    Provide a user service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return UserService(
        user_repo=user_repo,
        org_repo=org_repo,
        warehouse_repo=warehouse_repo,
        rbac_repo=rbac_repo,
    )
