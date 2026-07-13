"""Manage database interactions for organizations.

This module encapsulates data access for the Organization model, representing
top-level tenants in the multi-tenant architecture. It handles queries for
creating and fetching root organizational records.
"""

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.organization import Organization
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class OrganizationRepository:
    """Manage data access for Organization entities.

    This repository performs CRUD operations on the top-level Organization
    model. It is central to tenant isolation since most other models link
    back to an organization.
    """

    async def create(
        self, db: AsyncSession, organization: Organization
    ) -> Organization:
        """Stage a new organization record for insertion into the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization (Organization): The organization entity to create.

        Returns:
            Organization: The staged organization instance.
        """
        db.add(organization)
        return organization

    async def get_by_id(
        self, db: AsyncSession, organization_id: int
    ) -> Organization | None:
        """Fetch a specific organization by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The unique identifier of the organization.

        Returns:
            Organization | None: The requested organization, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(Organization, organization_id)

    async def get_all(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[Organization], int]:
        """Fetch a paginated list of all active organizations.

        Used typically by super-admin roles to review all registered tenants
        across the platform.

        Args:
            db (AsyncSession): The active asynchronous database session.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Organization], int]: The fetched organizations and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = select(Organization).order_by(Organization.id)
        items, total = await paginate_query(db, query, params)
        return items, total

    async def delete(self, db: AsyncSession, organization: Organization) -> None:
        """Stage an organization record for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization (Organization): The organization entity to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(organization)
