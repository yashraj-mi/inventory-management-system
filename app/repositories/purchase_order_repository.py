"""Manage database interactions for purchase orders.

This module provides the PurchaseOrderRepository, isolating the database
logic needed to manage incoming stock requests and procurement from external
suppliers.
"""

from app.repositories.base_repository import BaseRepository
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.purchase_order import PurchaseOrder
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    """Manage data access for PurchaseOrder entities.

    Handles creation, lookup by specific business identifiers, and paginated
    retrieval for warehouse-scoped purchase tracking.
    """

    model = PurchaseOrder

    async def get_by_po_number(
        self, db: AsyncSession, po_number: str
    ) -> PurchaseOrder | None:
        """Fetch a purchase order using its unique PO number.

        Used for external integrations, supplier communications, or barcode
        scanning lookups.

        Args:
            db (AsyncSession): The active asynchronous database session.
            po_number (str): The unique business identifier for the order.

        Returns:
            PurchaseOrder | None: The matching purchase order, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        )

    async def get_all_by_warehouse(
        self, db: AsyncSession, warehouse_id: int, params: PaginationParams
    ) -> tuple[Sequence[PurchaseOrder], int]:
        """Fetch a paginated list of purchase orders destined for a specific warehouse.

        Ordered descending by ID to present the most recently created orders first.

        Args:
            db (AsyncSession): The active asynchronous database session.
            warehouse_id (int): The destination warehouse ID.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[PurchaseOrder], int]: The fetched orders and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(PurchaseOrder)
            .where(PurchaseOrder.destination_warehouse_id == warehouse_id)
            .order_by(PurchaseOrder.id.desc())
        )
        return await paginate_query(db, query, params)
