"""Manage database interactions for sales order line items.

This module encapsulates queries related to individual line items within an
outbound sales order, handling creation, retrieval, and deletion of products
requested by a customer.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sales_order_item import SalesOrderItem


class SalesOrderItemRepository:
    """Manage data access for SalesOrderItem records.

    Provides database access methods for line items, supporting inventory
    allocation and order fulfillment processes.
    """

    async def create(
        self, db: AsyncSession, item_data: SalesOrderItem
    ) -> SalesOrderItem:
        """Stage a single sales order line item for insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            item_data (SalesOrderItem): The order item to insert.

        Returns:
            SalesOrderItem: The staged item instance.
        """
        db.add(item_data)
        return item_data

    async def get_by_id(self, db: AsyncSession, item_id: int) -> SalesOrderItem | None:
        """Fetch a specific sales order line item by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            item_id (int): The unique identifier of the line item.

        Returns:
            SalesOrderItem | None: The requested line item, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(SalesOrderItem, item_id)

    async def get_all_by_sales_order(
        self, db: AsyncSession, sales_order_id: int
    ) -> Sequence[SalesOrderItem]:
        """Fetch all line items associated with a given sales order.

        Retrieves the complete list of products requested in an order to
        calculate totals or drive the picking process.

        Args:
            db (AsyncSession): The active asynchronous database session.
            sales_order_id (int): The ID of the parent sales order.

        Returns:
            Sequence[SalesOrderItem]: A sequence of associated order items.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        result = await db.scalars(
            select(SalesOrderItem).where(
                SalesOrderItem.sales_order_id == sales_order_id
            )
        )
        return result.all()

    async def delete(self, db: AsyncSession, item_record: SalesOrderItem) -> None:
        """Stage a sales order line item for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            item_record (SalesOrderItem): The item instance to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(item_record)
