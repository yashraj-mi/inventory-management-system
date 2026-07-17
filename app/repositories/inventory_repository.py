"""Manage database interactions for physical inventory.

This module provides repository methods to handle stock levels, batches, and
warehouse assignments, including locking mechanisms to prevent race conditions
during order fulfillment.
"""

from app.repositories.base_repository import BaseRepository
from collections.abc import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory import Inventory
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query
from app.constants.inventory_enum import InventoryStatus


class InventoryRepository(BaseRepository[Inventory]):
    """Manage data access for Inventory records.

    Handles creation, retrieval, and deletion of inventory items. Supports
    pessimistic locking and aggregation queries to determine available stock.
    """

    model = Inventory

    async def get_by_unique_key(
        self, db: AsyncSession, warehouse_id: int, product_id: int, batch_number: str
    ) -> Inventory | None:
        """Fetch an inventory batch assignment with an exclusive lock.

        Uses pessimistic locking (`FOR UPDATE`) to prevent race conditions when
        multiple transactions attempt to modify the same batch simultaneously.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The ID of the warehouse storing the product.
            product_id (int): The ID of the product.
            batch_number (str): The specific batch identifier.

        Returns:
            Inventory | None: The locked inventory instance, or None if not found.

        Raises:
            SQLAlchemyError: If the database query fails or the lock times out.
        """
        return await db.scalar(
            select(Inventory)
            .where(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id,
                Inventory.batch_number == batch_number,
            )
            .with_for_update()
        )

    async def get_all_by_warehouse(
        self, db: AsyncSession, warehouse_id: int, params: PaginationParams
    ) -> tuple[Sequence[Inventory], int]:
        """Fetch a paginated list of all inventory items within a warehouse.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The ID of the warehouse.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Inventory], int]: The fetched inventory records and total count.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        query = (
            select(Inventory)
            .where(Inventory.warehouse_id == warehouse_id)
            .order_by(Inventory.id)
        )
        return await paginate_query(db, query, params)

    async def get_all_by_product(
        self, db: AsyncSession, product_id: int, params: PaginationParams
    ) -> tuple[Sequence[Inventory], int]:
        """Fetch a paginated list of inventory records globally for a product.

        Results are ordered by expiry date to support FEFO (First Expired, First Out)
        views or reporting.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The ID of the product.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Inventory], int]: The fetched inventory records and total count.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        query = (
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .order_by(Inventory.expiry_date)
        )
        return await paginate_query(db, query, params)

    async def get_warehouse_inventory_by_product(
        self, db: AsyncSession, product_id: int, warehouse_id: int
    ) -> list[Inventory]:
        """Fetch and lock all available inventory batches for a product in a warehouse.

        Retrieves all batches of a specific product at a specific location, ordered
        by expiry date, and applies a pessimistic lock (`FOR UPDATE`) for allocation.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The ID of the requested product.
            warehouse_id (int): The ID of the target warehouse.

        Returns:
            list[Inventory]: A list of locked inventory records.

        Raises:
            SQLAlchemyError: If the database query fails or locking times out.
        """
        query = (
            select(Inventory)
            .where(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id,
            )
            .order_by(Inventory.expiry_date)
            .with_for_update()
        )
        return list(await db.scalars(query))

    async def get_warehouse_product(
        self, db: AsyncSession, product_id: int, warehouse_id: int
    ) -> int | None:
        """Calculate the total available quantity of a product in a warehouse.

        Aggregates the difference between physical quantity and reserved quantity
        across all active batches.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The ID of the requested product.
            warehouse_id (int): The ID of the target warehouse.

        Returns:
            int | None: The aggregated available stock, or None if no active inventory exists.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        query = select(
            func.sum(Inventory.quantity - Inventory.reserved_quantity)
        ).where(
            Inventory.product_id == product_id,
            Inventory.status == InventoryStatus.ACTIVE,
            Inventory.warehouse_id == warehouse_id,
        )

        return await db.scalar(query)
