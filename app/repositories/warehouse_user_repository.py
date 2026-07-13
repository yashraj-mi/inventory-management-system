"""Manage database interactions for warehouse role assignments.

This module provides the WarehouseUserRepository for creating, checking, and
removing permissions that authorize specific users to operate within specific
warehouses.
"""

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.warehouse_users import WarehouseUsers
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class WarehouseUserRepository:
    """Manage data access for WarehouseUser linking records.

    Handles the bidirectional lookup and assignment of personnel to distinct
    physical locations within an organization.
    """

    async def get_assignment(
        self, db: AsyncSession, warehouse_id: int, user_id: int
    ) -> WarehouseUsers | None:
        """Fetch a specific mapping entry for a target warehouse and user.

        Used to verify if a user has operational authorization for a given
        warehouse facility.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The ID of the targeted warehouse.
            user_id (int): The ID of the queried user.

        Returns:
            WarehouseUsers | None: The mapping entry, or None if not assigned.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        result = await db.execute(
            select(WarehouseUsers).where(
                WarehouseUsers.warehouse_id == warehouse_id,
                WarehouseUsers.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def list_by_warehouse(
        self, db: AsyncSession, warehouse_id: int, params: PaginationParams
    ) -> tuple[Sequence[WarehouseUsers], int]:
        """Fetch a paginated list of all personnel mapped to a specific warehouse.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The ID of the target warehouse.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[WarehouseUsers], int]: The fetched mapping entries and total count.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        query = select(WarehouseUsers).where(
            WarehouseUsers.warehouse_id == warehouse_id
        )
        return await paginate_query(db, query, params)

    async def add(self, db: AsyncSession, assignment: WarehouseUsers) -> WarehouseUsers:
        """Stage a new warehouse user assignment record for insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            assignment (WarehouseUsers): The mapping entity to insert.

        Returns:
            WarehouseUsers: The staged mapping entity.
        """
        db.add(assignment)
        return assignment

    async def delete(self, db: AsyncSession, assignment: WarehouseUsers) -> None:
        """Stage a warehouse user assignment row for deletion.

        Effectively revokes a user's access to operate within the linked warehouse.

        Args:
            db (AsyncSession): The active asynchronous database session.
            assignment (WarehouseUsers): The mapping entity to delete.

        Raises:
            SQLAlchemyError: If the deletion staging fails.
        """
        await db.delete(assignment)
