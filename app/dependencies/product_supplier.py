"""
Dependency injection module for product_supplier.py.

Provides FastAPI dependencies for product_supplier components.
"""

from fastapi import Depends

from app.repositories.product_supplier_repository import ProductSupplierRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.product_supplier_service import ProductSupplierService
from app.dependencies.supplier import get_supplier_repo


def get_product_supplier_repo() -> ProductSupplierRepository:
    """
    Provide a product_supplier repository instance.

    Returns:
        Repository instance for database operations.
    """
    return ProductSupplierRepository()


def _get_product_repo() -> ProductRepository:
    """
    Provide a _product repository instance.

    Returns:
        Repository instance for database operations.
    """
    return ProductRepository()


def get_product_supplier_service(
    product_supplier_repo: ProductSupplierRepository = Depends(
        get_product_supplier_repo
    ),
    product_repo: ProductRepository = Depends(_get_product_repo),
    supplier_repo: SupplierRepository = Depends(get_supplier_repo),
) -> ProductSupplierService:
    """
    Provide a product_supplier service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return ProductSupplierService(
        repo=product_supplier_repo,
        product_repo=product_repo,
        supplier_repo=supplier_repo,
    )
