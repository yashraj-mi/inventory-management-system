"""
Dependency injection module for product.py.

Provides FastAPI dependencies for product components.
"""

from fastapi import Depends

from app.repositories.product_repository import ProductRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.category_repository import CategoryRepository
from app.services.product_supplier_service import ProductSupplierService
from app.services.product_service import ProductService

from app.dependencies.organization import get_organization_repo
from app.dependencies.category import get_category_repo
from app.dependencies.product_supplier import get_product_supplier_service


def get_product_repo() -> ProductRepository:
    """
    Provide a product repository instance.

    Returns:
        Repository instance for database operations.
    """
    return ProductRepository()


def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    product_supplier_service: ProductSupplierService = Depends(
        get_product_supplier_service
    ),
) -> ProductService:
    """
    Provide a product service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return ProductService(
        product_repo=product_repo,
        org_repo=org_repo,
        category_repo=category_repo,
        product_supplier_service=product_supplier_service,
    )
