"""
Dependency injection module for warehouse.py.

Provides FastAPI dependencies for warehouse components.
"""

from fastapi import Depends

from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.warehouse_service import WarehouseService
from app.dependencies.organization import get_organization_repo


def get_warehouse_repo() -> WarehouseRepository:
    """
    Provide a warehouse repository instance.

    Returns:
        Repository instance for database operations.
    """
    return WarehouseRepository()


def get_warehouse_service(
    warehouse_repo: WarehouseRepository = Depends(get_warehouse_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
) -> WarehouseService:
    """
    Provide a warehouse service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return WarehouseService(warehouse_repo=warehouse_repo, org_repo=org_repo)
