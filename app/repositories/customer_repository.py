"""Manage database interactions for customer entities.

This module provides the CustomerRepository, encapsulating the database
queries required to manage client profiles and support order management,
while maintaining multi-tenant organization isolation.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.customer import Customer
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class CustomerRepository:
    """Manage data access for Customer records.

    Handles insertion, retrieval, and deletion of customer profiles, ensuring
    queries correctly filter by organization ID to enforce data boundaries.
    """

    async def create(self, db: AsyncSession, customer_data: Customer) -> Customer:
        """Stage a new customer record for insertion into the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            customer_data (Customer): The customer entity to insert.

        Returns:
            Customer: The staged customer instance.
        """
        db.add(customer_data)
        return customer_data

    async def get_by_id(self, db: AsyncSession, customer_id: int) -> Customer | None:
        """Fetch a specific customer by their primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            customer_id (int): The unique identifier of the customer.

        Returns:
            Customer | None: The requested customer, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(Customer, customer_id)

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

    async def get_all(
        self, db: AsyncSession, organization_id: int, params: PaginationParams
    ) -> tuple[Sequence[Customer], int]:
        """Fetch a paginated list of all customers belonging to an organization.

        Provides data for customer directory views and reporting tools, sorted
        by the underlying primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Customer], int]: The fetched customers and the total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(Customer)
            .where(Customer.organization_id == organization_id)
            .order_by(Customer.id)
        )
        return await paginate_query(db, query, params)

    async def delete(self, db: AsyncSession, customer_record: Customer) -> None:
        """Stage a customer record for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            customer_record (Customer): The customer instance to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(customer_record)
