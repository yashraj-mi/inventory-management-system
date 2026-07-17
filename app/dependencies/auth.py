"""
Dependency injection module for auth.py.

Provides FastAPI dependencies for auth components.
"""

from fastapi import Depends


from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService
from app.dependencies.organization import get_organization_repo
from app.repositories.organization_repository import OrganizationRepository


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
