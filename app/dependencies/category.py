"""
Dependency injection module for category.py.

Provides FastAPI dependencies for category components.
"""

from fastapi import Depends

from app.repositories.category_repository import CategoryRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.category_service import CategoryService
from app.dependencies.organization import get_organization_repo


def get_category_repo() -> CategoryRepository:
    """
    Provide a category repository instance.

    Returns:
        Repository instance for database operations.
    """
    return CategoryRepository()


def get_category_service(
    category_repo: CategoryRepository = Depends(get_category_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
) -> CategoryService:
    """
    Provide a category service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return CategoryService(category_repo=category_repo, org_repo=org_repo)
