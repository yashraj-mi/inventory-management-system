"""
Dependency injection module for organization.py.

Provides FastAPI dependencies for organization components.
"""

from fastapi import Depends

from app.repositories.organization_repository import OrganizationRepository
from app.services.organization_service import OrganizationService


def get_organization_repo() -> OrganizationRepository:
    """
    Provide a organization repository instance.

    Returns:
        Repository instance for database operations.
    """
    return OrganizationRepository()


def get_organization_service(
    organization_repo: OrganizationRepository = Depends(get_organization_repo),
) -> OrganizationService:
    """
    Provide a organization service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return OrganizationService(organization_repo)
