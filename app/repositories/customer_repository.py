"""Manage database interactions for customer entities.

This module provides the CustomerRepository, encapsulating the database
queries required to manage client profiles and support order management,
while maintaining multi-tenant organization isolation.
"""

from app.repositories.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.customer import Customer


class CustomerRepository(BaseRepository[Customer]):
    """Manage data access for Customer records.

    Handles insertion, retrieval, and deletion of customer profiles, ensuring
    queries correctly filter by organization ID to enforce data boundaries.
    """

    model = Customer

    async def get_by_email(
        self, db: AsyncSession, organization_id: int, email: str
    ) -> Customer | None:
        """Fetch a customer by their email address within an organization.

        Used to validate email uniqueness and look up client profiles during
        order entry or authentication processes.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            email (str): The email address to search for.

        Returns:
            Customer | None: The matching customer, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(Customer).where(
                Customer.organization_id == organization_id, Customer.email == email
            )
        )

    async def get_by_phone(
        self, db: AsyncSession, organization_id: int, phone: str
    ) -> Customer | None:
        """Fetch a customer by their phone number within an organization.

        Validates phone uniqueness or supports caller-ID lookups.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            phone (str): The phone number to search for.

        Returns:
            Customer | None: The matching customer, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(Customer).where(
                Customer.organization_id == organization_id, Customer.phone == phone
            )
        )
