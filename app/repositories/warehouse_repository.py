"""Manage database interactions for physical warehouse locations.

This module provides the WarehouseRepository, handling data access for warehouse
definitions, tracking locations where inventory is stored, shipped, and received.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.warehouse import Warehouse
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class WarehouseRepository:
    """Manage data access for Warehouse entities.

    Facilitates querying warehouse facilities, providing tenant isolation
    by filtering on organization ID.
    """

    async def create(self, db: AsyncSession, warehouse: Warehouse) -> Warehouse:
        """Stage a new warehouse record for database insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse (Warehouse): The warehouse entity to create.

        Returns:
            Warehouse: The staged warehouse instance.
        """
        db.add(warehouse)
        return warehouse

    async def get_all(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[Warehouse], int]:
        """Fetch a paginated list of all system warehouses globally.

        Primarily used by super-admin roles to audit warehouse usage across
        all platform organizations.

        Args:
            db (AsyncSession): The active asynchronous database session.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Warehouse], int]: The fetched warehouses and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = select(Warehouse)
        return await paginate_query(db, query, params)

    async def get_by_id(self, db: AsyncSession, warehouse_id: int) -> Warehouse | None:
        """Fetch a specific warehouse by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The unique identifier of the warehouse.

        Returns:
            Warehouse | None: The requested warehouse, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(Warehouse, warehouse_id)

    async def get_by_code(
        self, db: AsyncSession, organization_id: int, code: str
    ) -> Warehouse | None:
        """Fetch a warehouse by its unique code within an organization.

        Ensures code uniqueness per organization and allows quick facility
        lookups via external integration keys.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            code (str): The specific warehouse code.

        Returns:
            Warehouse | None: The matching warehouse, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        stmt = select(Warehouse).where(
            Warehouse.organization_id == organization_id, Warehouse.code == code
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self, db: AsyncSession, organization_id: int, params: PaginationParams
    ) -> tuple[Sequence[Warehouse], int]:
        """Fetch a paginated list of warehouses scoped to a specific organization.

        Enforces tenant isolation by retrieving only the facilities belonging
        to the specified organization.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Warehouse], int]: The fetched warehouses and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = select(Warehouse).where(Warehouse.organization_id == organization_id)
        return await paginate_query(db, query, params)

    async def update(self, db: AsyncSession, warehouse: Warehouse) -> Warehouse:
        """Process updates for an existing warehouse record.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse (Warehouse): The warehouse entity to update.

        Returns:
            Warehouse: The updated warehouse instance.
        """
        return warehouse

    async def delete(self, db: AsyncSession, warehouse: Warehouse) -> None:
        """Stage a warehouse record for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse (Warehouse): The warehouse entity to delete.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(warehouse)
