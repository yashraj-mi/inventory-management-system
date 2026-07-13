"""
Sales order item service.

Handles the creation and retrieval of line items associated with a sales order,
including tracking specific batches and unit prices at the time of sale.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Sequence
from app.repositories.sales_order_item_repository import SalesOrderItemRepository
from app.schemas.sales_order import SalesOrderItemCreateInternal, SalesOrderItemResponse
from app.db.models.sales_order_item import SalesOrderItem


class SalesOrderItemService:
    """Service layer managing line items for outbound sales."""

    def __init__(self, repo: SalesOrderItemRepository) -> None:
        """
        Initialize the SalesOrderItemService.

        Args:
            repo: Data access layer for sales order line items.
        """
        self.repo = repo

    async def create(
        self, db: AsyncSession, payload: SalesOrderItemCreateInternal
    ) -> None:
        """
        Persist multiple line items for a newly created sales order.

        Args:
            db: Active DB session.
            payload: Validated payload containing products, quantities, and prices.
        """
        for item in payload.items:
            record = SalesOrderItem(
                sales_order_id=payload.sales_order_id,
                product_id=item.product_id,
                batch_number=item.batch_number,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            await self.repo.create(db, record)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            from fastapi import status
            from app.core.exceptions import AppException
            from app.constants.common_enum import CrudMessages

            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Sales Order Item"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except Exception:
            await db.rollback()
            from fastapi import status
            from app.core.exceptions import AppException
            from app.constants.common_enum import CrudMessages

            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Sales Order Item", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def _get_order_items(
        self, db: AsyncSession, sales_order_id: int
    ) -> Sequence[SalesOrderItem]:
        return await self.repo.get_all_by_sales_order(db, sales_order_id)

    async def get_order_items(
        self, db: AsyncSession, sales_order_id: int
    ) -> Sequence[SalesOrderItemResponse]:
        """
        Retrieve line items for a sales order as public response schemas.

        Args:
            db: Active DB session.
            sales_order_id: Target sales order ID.

        Returns:
            Sequence of SalesOrderItemResponse models.
        """
        items = await self._get_order_items(db, sales_order_id)
        return [SalesOrderItemResponse.model_validate(item) for item in items]
