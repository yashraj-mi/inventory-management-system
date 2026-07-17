"""Manage database interactions for vendor and supplier profiles.

This module provides the SupplierRepository, encapsulating the data access
logic required to maintain supplier contact information and support procurement
workflows within specific organizations.
"""

from app.repositories.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.supplier import Supplier


class SupplierRepository(BaseRepository[Supplier]):
    """Manage data access for Supplier records.

    Handles creation, pagination, and uniqueness validation queries (e.g.,
    email and phone) for suppliers tied to a specific organization.
    """

    model = Supplier

    async def get_by_email(
        self, db: AsyncSession, org_id: int, email: str
    ) -> Supplier | None:
        """Fetch a supplier by their email address within an organization.

        Used to validate email uniqueness during vendor onboarding or updates.

        Args:
            db (AsyncSession): The active asynchronous database session.
            org_id (int): The ID of the parent organization.
            email (str): The email address to search for.

        Returns:
            Supplier | None: The matching supplier, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(Supplier).where(
                Supplier.organization_id == org_id, Supplier.email == email
            )
        )

    async def get_by_phone(
        self, db: AsyncSession, org_id: int, phone: str
    ) -> Supplier | None:
        """Fetch a supplier by their phone number within an organization.

        Used to validate phone uniqueness during vendor onboarding or updates.

        Args:
            db (AsyncSession): The active asynchronous database session.
            org_id (int): The ID of the parent organization.
            phone (str): The phone number to search for.

        Returns:
            Supplier | None: The matching supplier, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(Supplier).where(
                Supplier.organization_id == org_id, Supplier.phone == phone
            )
        )
