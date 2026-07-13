"""Manage database interactions for backorders.

This module provides repository methods to handle backorder models, isolating
database query logic from the business services. Backorders track products that
could not be fulfilled immediately during sales order processing.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.backorder import Backorder
from app.constants.sales_order_enum import BackorderStatus


class BackorderRepository:
    """Manage data access operations for the Backorder entity.

    Handles creation, retrieval, and deletion of backorder records, as well as
    fetching waiting backorders by product or sales order.
    """

    async def create(self, db: AsyncSession, backorder_data: Backorder) -> Backorder:
        """Add a new backorder record to the database session.

        Stages a backorder entity to be inserted into the database. Does not
        commit the transaction, leaving that to the calling service.

        Args:
            db (AsyncSession): The active asynchronous database session.
            backorder_data (Backorder): The backorder model instance to insert.

        Returns:
            Backorder: The staged backorder instance.
        """
        db.add(backorder_data)
        return backorder_data

    async def get_by_id(self, db: AsyncSession, backorder_id: int) -> Backorder | None:
        """Retrieve a specific backorder by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            backorder_id (int): The unique identifier of the backorder.

        Returns:
            Backorder | None: The requested backorder, or None if not found.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        return await db.get(Backorder, backorder_id)

    async def get_all_by_sales_order(
        self, db: AsyncSession, sales_order_id: int
    ) -> Sequence[Backorder]:
        """Fetch all backorders associated with a given sales order.

        Retrieves every backorder linked to the specified sales order,
        regardless of their current status.

        Args:
            db (AsyncSession): The active asynchronous database session.
            sales_order_id (int): The ID of the parent sales order.

        Returns:
            Sequence[Backorder]: A sequence of associated backorder records.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        result = await db.scalars(
            select(Backorder).where(Backorder.sales_order_id == sales_order_id)
        )
        return result.all()

    async def get_by_sales_order(
        self, db: AsyncSession, sales_order_id: int
    ) -> list[Backorder]:
        """Fetch all waiting backorders for a specific sales order.

        Filters backorders by the specified sales order ID and restricts the
        results to only those currently in the 'WAITING' status.

        Args:
            db (AsyncSession): The active asynchronous database session.
            sales_order_id (int): The ID of the parent sales order.

        Returns:
            list[Backorder]: A list of backorders waiting for fulfillment.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        query = select(Backorder).where(
            Backorder.sales_order_id == sales_order_id,
            Backorder.status == BackorderStatus.WAITING,
        )
        result = await db.scalars(query)
        return list(result.all())

    async def delete(self, db: AsyncSession, backorder_record: Backorder) -> None:
        """Remove a backorder record from the database session.

        Stages a specific backorder entity for deletion. The actual removal
        happens when the transaction is committed by the calling service.

        Args:
            db (AsyncSession): The active asynchronous database session.
            backorder_record (Backorder): The backorder instance to delete.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        await db.delete(backorder_record)

    async def get_by_product(
        self, db: AsyncSession, product_id: int, warehouse_id: int
    ) -> list[Backorder]:
        """Fetch waiting backorders for a specific product and warehouse.

        Retrieves backorders awaiting fulfillment for a specific product at a
        given warehouse, ordered by their expected date. Acquires a pessimistic
        lock (`FOR UPDATE`) on the records to prevent concurrent modification.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The ID of the backordered product.
            warehouse_id (int): The ID of the warehouse fulfilling the product.

        Returns:
            list[Backorder]: A list of locked, waiting backorders sorted by expected date.

        Raises:
            SQLAlchemyError: If a database operation fails or locking times out.
        """
        query = (
            select(Backorder)
            .where(
                Backorder.product_id == product_id,
                Backorder.warehouse_id == warehouse_id,
                Backorder.status == BackorderStatus.WAITING,
            )
            .order_by(Backorder.expected_by)
            .with_for_update()
        )
        result = await db.scalars(query)
        return list(result.all())
