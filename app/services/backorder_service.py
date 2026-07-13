"""
Backorder service managing fulfillment of out-of-stock items.

Handles creation, settlement, and cancellation of backorders when
inventory levels fail to meet sales order demand. Integrates with
InventoryService to track availability and SalesOrderService to
update status upon allocation.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status
from app.core.exceptions import AppException
from app.core.profiling import log_timing
from app.repositories.backorder_repository import BackorderRepository
from app.schemas.backorder import BackorderCreate, BackorderResponse
from app.db.models.backorder import Backorder
from app.constants.sales_order_enum import (
    BackorderStatus,
    SalesOrderStatus,
    BackorderMessages,
)
from app.schemas.sales_order import SalesOrderStatusUpdate
from app.services.inventory_service import InventoryService
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.services.sales_order_service import SalesOrderService


class BackorderService:
    """Service layer for backorder operations and auto-allocation rules."""

    def __init__(
        self,
        repo: BackorderRepository,
        inventory_service: InventoryService,
        sales_order_service: "SalesOrderService",
    ) -> None:
        """
        Initialize the BackorderService with dependencies.

        Args:
            repo: Repository for backorder persistence.
            inventory_service: Service to check and reserve inventory.
            sales_order_service: Service to update parent sales order state.
        """
        self.repo = repo
        self.inventory_service = inventory_service
        self.sales_order_service = sales_order_service

    async def _create(self, db: AsyncSession, payload: BackorderCreate) -> Backorder:
        """
        Create a new backorder record directly in the database.

        Args:
            db: Active database session.
            payload: Details of the backorder to create.

        Returns:
            The created Backorder entity.

        Raises:
            AppException: If foreign keys are invalid (409) or database error occurs (500).
        """
        record = Backorder(
            sales_order_id=payload.sales_order_id,
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            quantity_pending=payload.quantity_pending,
            expected_by=payload.expected_by,
            status=payload.status.value,
        )

        try:
            await self.repo.create(db, record)
            await db.flush()
            await db.refresh(record)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=BackorderMessages.CREATE_FK_ERROR,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=BackorderMessages.CREATE_UNEXPECTED_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return record

    async def create(
        self, db: AsyncSession, payload: BackorderCreate
    ) -> BackorderResponse:
        """
        Create a new backorder and return its public schema.

        Args:
            db: Active database session.
            payload: Details of the backorder to create.

        Returns:
            The validated BackorderResponse schema.
        """
        record = await self._create(db, payload)
        return BackorderResponse.model_validate(record)

    async def _get_by_id(self, db: AsyncSession, backorder_id: int) -> Backorder | None:
        """
        Retrieve a backorder entity by its unique ID.

        Args:
            db: Active database session.
            backorder_id: The ID of the backorder to fetch.

        Returns:
            The Backorder entity if found, else None.
        """
        return await self.repo.get_by_id(db, backorder_id)

    async def get_by_id(
        self, db: AsyncSession, backorder_id: int
    ) -> BackorderResponse | None:
        """
        Retrieve a backorder and return its public schema.

        Args:
            db: Active database session.
            backorder_id: The ID of the backorder to fetch.

        Returns:
            The BackorderResponse schema if found, else None.
        """
        record = await self._get_by_id(db, backorder_id)
        if record:
            return BackorderResponse.model_validate(record)
        return None

    @log_timing
    async def settle_backorders(
        self, db: AsyncSession, product_id: int, warehouse_id: int, actor_org_id: int
    ):
        """
        Settle existing backorders for a product when inventory is received.

        Checks pending backorders and automatically allocates available stock.
        Updates parent sales orders to CONFIRMED if all backorders are fulfilled.

        Args:
            db: Active database session.
            product_id: Product ID whose inventory was received.
            warehouse_id: Warehouse ID where inventory is stored.
            actor_org_id: The organization ID of the actor for permission checks.
        """
        backorders = await self.repo.get_by_product(db, product_id, warehouse_id)
        if backorders:
            for backorder in backorders:
                available_products = (
                    await self.inventory_service.get_warehouse_products(
                        db, product_id, warehouse_id
                    )
                )
                # Need to handle None returned by get_warehouse_products if no inventory exists
                if available_products is None:
                    available_products = 0
                if available_products >= backorder.quantity_pending:
                    await self.inventory_service.reserve_quantity(
                        db, product_id, warehouse_id, backorder.quantity_pending
                    )
                    backorder.status = BackorderStatus.ALLOCATED
                    backorder.quantity_pending = 0

                    if not await self.repo.get_by_sales_order(
                        db, backorder.sales_order_id
                    ):
                        so = await self.sales_order_service.get(
                            db, backorder.sales_order_id, actor_org_id
                        )
                        if so.status not in (
                            SalesOrderStatus.PARTIALLY_FULFILLED.value,
                            SalesOrderStatus.FULFILLED.value,
                            SalesOrderStatus.CANCELLED.value,
                        ):
                            payload = SalesOrderStatusUpdate(
                                status=SalesOrderStatus.CONFIRMED
                            )
                            await self.sales_order_service.update_status(
                                db, backorder.sales_order_id, payload, actor_org_id
                            )

                else:
                    await self.inventory_service.reserve_quantity(
                        db,
                        backorder.product_id,
                        backorder.warehouse_id,
                        available_products,
                    )

                    backorder.quantity_pending -= available_products

                try:
                    await db.flush()
                except IntegrityError:
                    await db.rollback()
                    raise AppException(
                        message=BackorderMessages.CREATE_FK_ERROR,
                        status_code=status.HTTP_409_CONFLICT,
                    )
                except SQLAlchemyError:
                    await db.rollback()
                    raise AppException(
                        message=BackorderMessages.CREATE_UNEXPECTED_ERROR,
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

    async def cancel_backorders_for_so(self, db: AsyncSession, sales_order_id: int):
        """
        Cancel all pending backorders associated with a specific sales order.

        Args:
            db: Active database session.
            sales_order_id: The ID of the sales order being cancelled.
        """
        backorders = await self.repo.get_by_sales_order(db, sales_order_id)
        for bo in backorders:
            bo.status = BackorderStatus.CANCELLED.value
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=BackorderMessages.CREATE_FK_ERROR,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=BackorderMessages.CREATE_UNEXPECTED_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
