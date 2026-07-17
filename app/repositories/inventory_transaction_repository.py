"""Manage database interactions for inventory ledger entries.

This module provides the InventoryTransactionRepository, abstracting the queries
used to record and retrieve historical movements of stock, ensuring a reliable
audit trail of inventory adjustments, receipts, and fulfillments.
"""

from app.repositories.base_repository import BaseRepository
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory_transaction import InventoryTransaction
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class InventoryTransactionRepository(BaseRepository[InventoryTransaction]):
    """Manage data access for InventoryTransaction records.

    Handles insertion and time-ordered retrieval of inventory ledger entries,
    supporting warehouse-specific or product-wide audit views.
    """

    model = InventoryTransaction

    async def get_all_by_warehouse(
        self, db: AsyncSession, warehouse_id: int, params: PaginationParams
    ) -> tuple[Sequence[InventoryTransaction], int]:
        """Fetch a paginated ledger of transactions for a specific warehouse.

        Retrieves all stock movements within a given warehouse, ordered in
        reverse chronological order (newest first).

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The ID of the target warehouse.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[InventoryTransaction], int]: The fetched transactions and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(InventoryTransaction)
            .where(InventoryTransaction.warehouse_id == warehouse_id)
            .order_by(InventoryTransaction.created_at.desc())
        )
        return await paginate_query(db, query, params)

    async def get_all_by_product(
        self, db: AsyncSession, product_id: int, params: PaginationParams
    ) -> tuple[Sequence[InventoryTransaction], int]:
        """Fetch a paginated ledger of transactions globally for a specific product.

        Retrieves all historical stock movements across all warehouses for the
        given product, ordered by descending creation time.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The ID of the queried product.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[InventoryTransaction], int]: The fetched transactions and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(InventoryTransaction)
            .where(InventoryTransaction.product_id == product_id)
            .order_by(InventoryTransaction.created_at.desc())
        )
        return await paginate_query(db, query, params)
