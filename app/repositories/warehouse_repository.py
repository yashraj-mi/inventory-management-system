"""Manage database interactions for physical warehouse locations.

This module provides the WarehouseRepository, handling data access for warehouse
definitions, tracking locations where inventory is stored, shipped, and received.
"""

from app.repositories.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.warehouse import Warehouse


class WarehouseRepository(BaseRepository[Warehouse]):
    """Manage data access for Warehouse entities.

    Facilitates querying warehouse facilities, providing tenant isolation
    by filtering on organization ID.
    """

    model = Warehouse

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
