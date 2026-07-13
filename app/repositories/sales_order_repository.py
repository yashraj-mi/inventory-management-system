"""Manage database interactions for sales orders.

This module provides the SalesOrderRepository, handling data access for outbound
customer orders to track fulfillments, packing slips, and order lifecycles.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sales_order import SalesOrder
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class SalesOrderRepository:
    """Manage data access for SalesOrder entities.

    Abstracts database operations for tracking customer orders, supporting
    warehouse-specific pagination and lookup by business-facing order numbers.
    """

    async def create(self, db: AsyncSession, so_data: SalesOrder) -> SalesOrder:
        """Stage a new sales order record for database insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            so_data (SalesOrder): The sales order entity to insert.

        Returns:
            SalesOrder: The staged sales order instance.
        """
        db.add(so_data)
        return so_data

    async def get_by_id(self, db: AsyncSession, so_id: int) -> SalesOrder | None:
        """Fetch a specific sales order by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            so_id (int): The unique identifier of the sales order.

        Returns:
            SalesOrder | None: The requested sales order, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(SalesOrder, so_id)

    async def get_by_order_number(
        self, db: AsyncSession, order_number: str
    ) -> SalesOrder | None:
        """Fetch a sales order using its unique business order number.

        Args:
            db (AsyncSession): The active asynchronous database session.
            order_number (str): The specific order number given to the customer.

        Returns:
            SalesOrder | None: The matching sales order, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(SalesOrder).where(SalesOrder.order_number == order_number)
        )

    async def get_all_by_warehouse(
        self, db: AsyncSession, warehouse_id: int, params: PaginationParams
    ) -> tuple[Sequence[SalesOrder], int]:
        """Fetch a paginated list of sales orders allocated to a specific warehouse.

        Ordered descending by ID to present the most recent orders first.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The ID of the fulfilling warehouse.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[SalesOrder], int]: The fetched orders and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(SalesOrder)
            .where(SalesOrder.source_warehouse_id == warehouse_id)
            .order_by(SalesOrder.id.desc())
        )
        return await paginate_query(db, query, params)

    async def delete(self, db: AsyncSession, so_record: SalesOrder) -> None:
        """Stage a sales order for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            so_record (SalesOrder): The sales order instance to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(so_record)
