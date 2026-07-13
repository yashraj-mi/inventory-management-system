"""Manage database interactions for vendor and supplier profiles.

This module provides the SupplierRepository, encapsulating the data access
logic required to maintain supplier contact information and support procurement
workflows within specific organizations.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.supplier import Supplier
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class SupplierRepository:
    """Manage data access for Supplier records.

    Handles creation, pagination, and uniqueness validation queries (e.g.,
    email and phone) for suppliers tied to a specific organization.
    """

    async def create(self, db: AsyncSession, supplier_data: Supplier) -> Supplier:
        """Stage a new supplier profile for database insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            supplier_data (Supplier): The supplier entity to insert.

        Returns:
            Supplier: The staged supplier instance.
        """
        db.add(supplier_data)
        return supplier_data

    async def get_all(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[Supplier], int]:
        """Fetch a paginated list of all suppliers belonging to an organization.

        Provides data for vendor directory views and reporting tools, sorted
        by the underlying primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            org_id (int): The ID of the parent organization.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Supplier], int]: The fetched suppliers and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(Supplier)
            .where(Supplier.organization_id == org_id)
            .order_by(Supplier.id)
        )
        return await paginate_query(db, query, params)

    async def get_by_id(self, db: AsyncSession, supplier_id: int) -> Supplier | None:
        """Fetch a specific supplier by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            Supplier | None: The requested supplier, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(Supplier, supplier_id)

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

    async def delete(self, db: AsyncSession, supplier: Supplier) -> None:
        """Stage a supplier profile for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            supplier (Supplier): The supplier instance to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(supplier)
