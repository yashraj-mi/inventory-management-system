"""
warehouse_user_repository.py module.

Provides core functionality and components for the warehouse_user_repository domain.
"""

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.warehouse_users import WarehouseUsers


class WarehouseUserRepository:
    """
    Handles raw database access execution for Warehouse User assignments.
    """

    async def get_assignment(
        self, db: AsyncSession, warehouse_id: int, user_id: int
    ) -> WarehouseUsers | None:
        """
        Checks if a user mapping entry already exists for a target warehouse.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse.
            user_id (int): The ID of the user.

        Returns:
            WarehouseUsers | None: The found mapping entry, or None if not assigned.
        """
        result = await db.execute(
            select(WarehouseUsers).where(
                WarehouseUsers.warehouse_id == warehouse_id,
                WarehouseUsers.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def list_by_warehouse(
        self, db: AsyncSession, warehouse_id: int
    ) -> Sequence[WarehouseUsers]:
        """
        Lists all user records currently mapped to a specific warehouse.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse.

        Returns:
            Sequence[WarehouseUsers]: A sequence of mapping entries for the warehouse.
        """
        result = await db.execute(
            select(WarehouseUsers).where(WarehouseUsers.warehouse_id == warehouse_id)
        )
        return result.scalars().all()

    async def add(self, db: AsyncSession, assignment: WarehouseUsers) -> WarehouseUsers:
        """
        Persists a brand new warehouse user assignment row.

        Args:
            db (AsyncSession): The active database session context.
            assignment (WarehouseUsers): The mapping entity to insert.

        Returns:
            WarehouseUsers: The inserted mapping entity.
        """
        db.add(assignment)
        await db.flush()
        return assignment

    async def delete(self, db: AsyncSession, assignment: WarehouseUsers) -> None:
        """
        Purges a warehouse mapping execution row from the database.

        Args:
            db (AsyncSession): The active database session context.
            assignment (WarehouseUsers): The mapping entity to delete.
        """
        await db.delete(assignment)
        await db.flush()
