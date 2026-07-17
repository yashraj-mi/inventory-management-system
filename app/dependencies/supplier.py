"""
Dependency injection module for supplier.py.

Provides FastAPI dependencies for supplier components.
"""

from fastapi import Depends

from app.repositories.supplier_repository import SupplierRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.supplier_service import SupplierService
from app.dependencies.organization import get_organization_repo


def get_supplier_repo() -> SupplierRepository:
    """
    Provide a supplier repository instance.

    Returns:
        Repository instance for database operations.
    """
    return SupplierRepository()


def get_supplier_service(
    supplier_repo: SupplierRepository = Depends(get_supplier_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
) -> SupplierService:
    """
    Provide a supplier service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return SupplierService(supplier_repo=supplier_repo, org_repo=org_repo)
