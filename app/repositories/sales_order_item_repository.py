"""Manage database interactions for sales order line items.

This module encapsulates queries related to individual line items within an
outbound sales order, handling creation, retrieval, and deletion of products
requested by a customer.
"""

from app.repositories.base_repository import BaseRepository
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sales_order_item import SalesOrderItem


class SalesOrderItemRepository(BaseRepository[SalesOrderItem]):
    """Manage data access for SalesOrderItem records.

    Provides database access methods for line items, supporting inventory
    allocation and order fulfillment processes.
    """

    model = SalesOrderItem

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
