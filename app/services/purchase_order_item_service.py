"""
Purchase order item service.

Manages line items associated with purchase orders. Fetches negotiated cost
prices from supplier mappings and calculates initial line items.
"""

from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.exceptions import AppException
from app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from app.schemas.purchase_order import PurchaseOrderItemCreateInternal
from app.db.models.purchase_order_item import PurchaseOrderItem
from app.schemas.purchase_order import PurchaseOrderItemResponse


class PurchaseOrderItemService:
    """Service handling lifecycle of purchase order line items."""

    def __init__(self, repo: PurchaseOrderItemRepository):
        """
        Initialize the PurchaseOrderItemService.

        Args:
            repo: Data access layer for purchase order line items.
        """
        self.repo = repo

    async def create(self, db: AsyncSession, payload: PurchaseOrderItemCreateInternal):
        """
        Create multiple line items for a purchase order.

        Fetches pre-negotiated cost prices from the supplier mapping.

        Args:
            db: Active DB session.
            payload: Payload containing products and quantities.

        Raises:
            AppException: If a cost price mapping does not exist for a product.
        """
        product_ids = [item.product_id for item in payload.items]
        price_map = await self.repo.get_supplier_price(
            db, payload.supplier_id, product_ids
        )

        po_items_to_create = []
        for item in payload.items:
            cost_price = price_map.get(item.product_id)
            if not cost_price:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Product price not found for product_id={item.product_id}",
                )
            po_items_to_create.append(
                PurchaseOrderItem(
                    po_id=payload.po_id,
                    product_id=item.product_id,
                    unit_price=cost_price,
                    quantity=item.quantity,
                    received_quantity=0,
                )
            )

        await self.repo.bulk_create(db, po_items_to_create)

    async def update_items(
        self, db: AsyncSession, payload: PurchaseOrderItemCreateInternal
    ):
        """
        Update line items differentially for a draft purchase order.

        Updates quantities if modified, and generates new items for products
        not currently in the order.

        Args:
            db: Active DB session.
            payload: New set of desired line items and their quantities.
        """
        existing_items = await self._get_order_items(db, payload.po_id)
        existing_map = {item.product_id: item for item in existing_items}

        new_items_to_add = []
        for new_item in payload.items:
            if new_item.product_id in existing_map:
                existing_item = existing_map[new_item.product_id]
                if existing_item.quantity != new_item.quantity:
                    existing_item.quantity = new_item.quantity
            else:
                new_items_to_add.append(new_item)

        if new_items_to_add:
            new_payload = PurchaseOrderItemCreateInternal(
                po_id=payload.po_id,
                supplier_id=payload.supplier_id,
                items=new_items_to_add,
            )
            await self.create(db, new_payload)

        await db.flush()

    async def _get_order_items(self, db: AsyncSession, po_id: int):
        """
        Retrieve all line items linked to a purchase order.

        Args:
            db: Active DB session.
            po_id: ID of the purchase order.

        Returns:
            Sequence of PurchaseOrderItem models.
        """
        return await self.repo.get_order_items(db, po_id)

    async def get_order_items(
        self, db: AsyncSession, po_id: int
    ) -> Sequence[PurchaseOrderItemResponse]:
        """
        Retrieve order line items and return their public schema.

        Args:
            db: Active DB session.
            po_id: ID of the purchase order.

        Returns:
            List of PurchaseOrderItemResponse schemas.
        """
        items = await self._get_order_items(db, po_id)
        return [PurchaseOrderItemResponse.model_validate(item) for item in items]

    # Removed received_order since quantity is dynamically updated in the PO Service
