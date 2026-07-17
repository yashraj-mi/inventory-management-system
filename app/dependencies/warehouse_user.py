"""
Dependency injection module for warehouse_user.py.

Provides FastAPI dependencies for warehouse_user components.
"""

from fastapi import Depends

from app.repositories.warehouse_user_repository import WarehouseUserRepository
from app.services.warehouse_user_service import WarehouseUserService


def get_warehouse_user_repo() -> WarehouseUserRepository:
    """
    Provide a warehouse_user repository instance.

    Returns:
        Repository instance for database operations.
    """
    return WarehouseUserRepository()


def get_warehouse_user_service(
    warehouse_user_repo: WarehouseUserRepository = Depends(get_warehouse_user_repo),
) -> WarehouseUserService:
    """
    Provide a warehouse_user service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return WarehouseUserService(repo=warehouse_user_repo)
