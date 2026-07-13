"""Manage database interactions for purchase order line items.

This module encapsulates queries related to individual line items within a
purchase order, facilitating item creation, pricing lookups against supplier
catalogs, and bulk line item manipulations.
"""

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.purchase_order_item import PurchaseOrderItem
from app.db.models.product_supplier import ProductSupplier


class PurchaseOrderItemRepository:
    """Manage data access for PurchaseOrderItem records.

    Handles creation, bulk deletion, and pricing lookups for items added to
    a purchase order.
    """

    async def create(
        self, db: AsyncSession, item: PurchaseOrderItem
    ) -> PurchaseOrderItem:
        """Stage a single purchase order item for insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            item (PurchaseOrderItem): The order item to insert.

        Returns:
            PurchaseOrderItem: The staged item instance.
        """
        db.add(item)
        return item

    async def get_supplier_price(
        self, db: AsyncSession, supplier_id: int, product_ids: list[int]
    ):
        """Fetch agreed cost prices for a list of products from a specific supplier.

        Used to automatically price line items during purchase order creation based
        on existing vendor contracts (ProductSupplier mappings).

        Args:
            db (AsyncSession): The active asynchronous database session.
            supplier_id (int): The ID of the supplying vendor.
            product_ids (list[int]): A list of product IDs to price check.

        Returns:
            dict[int, float]: A dictionary mapping product IDs to their cost prices.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        stmt = select(ProductSupplier.product_id, ProductSupplier.cost_price).where(
            ProductSupplier.supplier_id == supplier_id,
            ProductSupplier.product_id.in_(product_ids),
        )

        result = await db.execute(stmt)
        return {row.product_id: float(row.cost_price) for row in result}

    async def bulk_create(self, db: AsyncSession, items: list[PurchaseOrderItem]):
        """Stage and flush multiple purchase order items simultaneously.

        Args:
            db (AsyncSession): The active asynchronous database session.
            items (list[PurchaseOrderItem]): The list of items to insert.

        Raises:
            SQLAlchemyError: If the database flush operation fails.
        """
        db.add_all(items)
        await db.flush()  # or commit(), depending on your transaction pattern

    async def delete_by_po_id(self, db: AsyncSession, po_id: int):
        """Delete all line items associated with a specific purchase order.

        Executes an immediate bulk deletion and flushes the session.

        Args:
            db (AsyncSession): The active asynchronous database session.
            po_id (int): The ID of the parent purchase order.

        Raises:
            SQLAlchemyError: If the database execution or flush fails.
        """
        stmt = delete(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po_id)
        await db.execute(stmt)
        await db.flush()

    async def get_order_items(self, db: AsyncSession, po_id: int):
        """Fetch all line items belonging to a specific purchase order.

        Args:
            db (AsyncSession): The active asynchronous database session.
            po_id (int): The ID of the parent purchase order.

        Returns:
            list[PurchaseOrderItem]: A list of associated purchase order items.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        stmt = select(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po_id)
        result = await db.execute(stmt)
        return result.scalars().all()  # <-- Add .scalars().all() here!

    # Removed received_order since quantity is dynamically updated in the PO Service
