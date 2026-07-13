"""
Dependency injection module for customer.py.

Provides FastAPI dependencies for customer components.
"""

from fastapi import Depends

from app.repositories.customer_repository import CustomerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.customer_service import CustomerService
from app.dependencies.organization import get_organization_repo


def get_customer_repo() -> CustomerRepository:
    """
    Provide a customer repository instance.

    Returns:
        Repository instance for database operations.
    """
    return CustomerRepository()


def get_customer_service(
    customer_repo: CustomerRepository = Depends(get_customer_repo),
    org_repo: OrganizationRepository = Depends(get_organization_repo),
) -> CustomerService:
    """
    Provide a customer service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return CustomerService(repo=customer_repo, org_repo=org_repo)
