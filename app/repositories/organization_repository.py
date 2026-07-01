"""
organization_repository.py module.

Provides core functionality and components for the organization_repository domain.
"""

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.organization import Organization


class OrganizationRepository:
    """
    Repository layer for managing Organization entities in the database.
    """

    async def create(
        self, db: AsyncSession, organization: Organization
    ) -> Organization:
        """
        Creates a new organization record in the database.

        Args:
            db (AsyncSession): The active database session context.
            organization (Organization): The organization entity to create.

        Returns:
            Organization: The created organization instance with its assigned ID.
        """
        db.add(organization)
        await db.flush()
        await db.refresh(organization)
        return organization

    async def get_by_id(
        self, db: AsyncSession, organization_id: int
    ) -> Organization | None:
        """
        Retrieves a single organization by its primary key.

        Args:
            db (AsyncSession): The active database session context.
            organization_id (int): The ID of the organization to fetch.

        Returns:
            Organization | None: The found organization, or None if it doesn't exist.
        """
        return await db.get(Organization, organization_id)

    async def get_all(self, db: AsyncSession) -> Sequence[Organization]:
        """
        Retrieves a paginated list of all organizations.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            Sequence[Organization]: A sequence of Organization instances.
        """
        result = await db.execute(select(Organization))
        return result.scalars().all()

    async def delete(self, db: AsyncSession, organization: Organization) -> None:
        """
        Deletes an organization record from the database.

        Args:
            db (AsyncSession): The active database session context.
            organization (Organization): The organization entity to delete.
        """
        await db.delete(organization)
        await db.flush()
