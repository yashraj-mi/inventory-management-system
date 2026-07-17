"""
Sales order service for managing outbound fulfillments.

Orchestrates the lifecycle of sales orders from drafting to confirmation and fulfillment.
Calculates stock availability, generates backorders when stock is insufficient, and
delegates to the inventory service for reservations and real deductions.
"""

from app.db.session_utils import db_transaction
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.constants.sales_order_enum import SalesOrderStatus, SalesOrderMessages
from app.repositories.sales_order_repository import SalesOrderRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.sales_order import SalesOrderCreateInternal
from app.db.models.sales_order import SalesOrder
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing
from app.services.sales_order_item_service import SalesOrderItemService
from app.schemas.sales_order import SalesOrderItemCreateInternal, SalesOrderStatusUpdate
from app.schemas.sales_order import SalesOrderResponse
from app.constants.sales_order_enum import so_allowed_transitions
from app.services.inventory_service import InventoryService
from app.constants.sales_order_enum import BackorderStatus
from app.schemas.backorder import BackorderCreate
from app.services.backorder_service import BackorderService
from app.schemas.sales_order import PartiallyFulfillPayload


class SalesOrderService:
    """
    Service layer for managing the lifecycle of sales orders.
    """

    def __init__(
        self,
        repo: SalesOrderRepository,
        warehouse_repo: WarehouseRepository,
        soi_service: SalesOrderItemService,
        inventory_service: InventoryService,
        backorder_service: BackorderService,
    ) -> None:
        """
        Initialize the SalesOrderService with required dependencies.

        Args:
            repo: Data access layer for sales orders.
            warehouse_repo: Repository to validate source warehouse ownership.
            soi_service: Service to manage line items for sales orders.
            inventory_service: Service to check stock and apply physical reservations/deductions.
            backorder_service: Service to handle insufficient stock automatically via backorders.
        """
        self.repo = repo
        self.warehouse_repo = warehouse_repo
        self.soi_service = soi_service
        self.inventory_service = inventory_service
        self.backorder_service = backorder_service

    def _generate_so_number(self) -> str:
        """
        Generate a unique, chronological order number for a new sales order.

        Returns:
            str: The generated sales order number.
        """
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"SO-{now_str}-{short_uuid}"

    @log_timing
    async def _create(
        self, db: AsyncSession, payload: SalesOrderCreateInternal
    ) -> SalesOrder:
        """
        Create a new draft sales order record directly in the database.

        Args:
            db: Active DB session.
            payload: Validated SO creation details.

        Returns:
            The created SalesOrder entity.

        Raises:
            AppException: If warehouse validation fails.
        """
        warehouse = await self.warehouse_repo.get_by_id(db, payload.source_warehouse_id)
        if not warehouse or warehouse.organization_id != payload.actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        so_number = self._generate_so_number()

        so_record = SalesOrder(
            customer_id=payload.customer_id,
            source_warehouse_id=payload.source_warehouse_id,
            order_number=so_number,
            due_date=payload.due_date,
            status=payload.status,
            created_by=payload.created_by,
        )

        async with db_transaction(db, module="Sales Order", action="operation"):
            await self.repo.create(db, so_record)
            await db.flush()
            await db.refresh(so_record)
        so_items = SalesOrderItemCreateInternal(
            sales_order_id=so_record.id, items=payload.items
        )

        await self.soi_service.create(db, so_items)

        await db.flush()
        await db.refresh(so_record, ["items"])

        return so_record

    @log_timing
    async def create(
        self, db: AsyncSession, payload: SalesOrderCreateInternal
    ) -> SalesOrderResponse:
        """
        Create a new sales order and return the public response schema.

        Args:
            db (AsyncSession): Active DB session.
            payload (SalesOrderCreateInternal): Validated SO creation details.

        Returns:
            SalesOrderResponse: The newly created sales order.
        """
        record = await self._create(db, payload)
        return SalesOrderResponse.model_validate(record)

    @log_timing
    async def _get(self, db: AsyncSession, so_id: int, actor_org_id: int) -> SalesOrder:
        """
        Internal method to fetch a raw SalesOrder ORM entity and validate organization access.

        Args:
            db (AsyncSession): Active DB session.
            so_id (int): The ID of the sales order.
            actor_org_id (int): The organization ID of the requesting user.

        Returns:
            SalesOrder: The fetched ORM entity.

        Raises:
            AppException: If not found or if the user lacks access.
        """
        record = await self.repo.get_by_id(db, so_id)
        if not record:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Sales Order"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        warehouse = await self.warehouse_repo.get_by_id(db, record.source_warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Sales Order"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return record

    @log_timing
    async def get(
        self, db: AsyncSession, so_id: int, actor_org_id: int
    ) -> SalesOrderResponse:
        """
        Fetch a single sales order by ID.

        Args:
            db (AsyncSession): Active DB session.
            so_id (int): The ID of the sales order.
            actor_org_id (int): The organization ID of the requesting user.

        Returns:
            SalesOrderResponse: The requested sales order data.
        """
        record = await self._get(db, so_id, actor_org_id)
        return SalesOrderResponse.model_validate(record)

    @log_timing
    async def get_by_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[list[SalesOrderResponse], int]:
        """
        Retrieve all sales orders originating from a specific warehouse.

        Args:
            db: Active DB session.
            warehouse_id: Target warehouse.
            actor_org_id: Organization ID of the requesting user.
            params: Pagination filters.

        Returns:
            A tuple of SalesOrderResponse schemas and total count.
        """
        warehouse = await self.warehouse_repo.get_by_id(db, warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        records, total = await self.repo.get_all_by_warehouse(db, warehouse_id, params)
        return [SalesOrderResponse.model_validate(r) for r in records], total

    @log_timing
    async def update_status(
        self,
        db: AsyncSession,
        sales_order_id: int,
        payload: SalesOrderStatusUpdate,
        actor_org_id: int,
    ) -> SalesOrderResponse:
        """
        Update the status of a sales order.

        Args:
            db (AsyncSession): Active DB session.
            sales_order_id (int): ID of the target sales order.
            payload (SalesOrderStatusUpdate): The new status to apply.
            actor_org_id (int): The organization ID of the requesting user.

        Returns:
            SalesOrderResponse: The updated sales order.

        Raises:
            AppException: For invalid transitions or insufficient privileges.
        """
        order = await self._get(db, sales_order_id, actor_org_id)

        if not order:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"There is not sales order found for id {sales_order_id}.",
            )

        if (
            order.status == SalesOrderStatus.PENDING
            and payload.status == SalesOrderStatus.CONFIRMED
        ):
            is_fully_confirmed = await self.confirm_order(db, order, actor_org_id)
            if not is_fully_confirmed:
                payload.status = SalesOrderStatus.AWAITING_CONFIRMED

        if payload.status not in so_allowed_transitions.get(order.status, []):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Can't change status from {order.status} to {payload.status.value}",
            )

        if payload.status == SalesOrderStatus.CANCELLED:
            if order.status in (
                SalesOrderStatus.AWAITING_CONFIRMED.value,
                SalesOrderStatus.CONFIRMED.value,
                SalesOrderStatus.PARTIALLY_FULFILLED.value,
            ):
                for item in order.items:
                    unfulfilled = item.quantity - item.fulfilled_quantity
                    if unfulfilled > 0:
                        await self.inventory_service.release_reserved_quantity(
                            db, item.product_id, order.source_warehouse_id, unfulfilled
                        )
            await self.backorder_service.cancel_backorders_for_so(db, order.id)

        order.status = payload.status

        async with db_transaction(db, module="Sales Order", action="operation"):
            await db.flush()
            await db.refresh(order)
        return SalesOrderResponse.model_validate(order)

    @log_timing
    async def confirm_order(self, db: AsyncSession, sales_order, actor_org_id: int):
        """
        Confirm a sales order, reserving stock and automatically generating backorders if necessary.

        Args:
            db (AsyncSession): Active DB session.
            sales_order: The sales order ORM entity.
            actor_org_id (int): The organization ID of the acting user.

        Returns:
            bool: True if the order can be fully fulfilled from current stock, False otherwise.
        """
        is_confirmed = True
        for item in sales_order.items:
            available_products = await self.inventory_service.get_warehouse_products(
                db, item.product_id, sales_order.source_warehouse_id
            )
            if available_products is None:
                available_products = 0

            if available_products >= item.quantity:
                await self.inventory_service.reserve_quantity(
                    db, item.product_id, sales_order.source_warehouse_id, item.quantity
                )
            else:
                await self.inventory_service.reserve_quantity(
                    db,
                    item.product_id,
                    sales_order.source_warehouse_id,
                    available_products,
                )
                payload = BackorderCreate(
                    sales_order_id=sales_order.id,
                    warehouse_id=sales_order.source_warehouse_id,
                    product_id=item.product_id,
                    quantity_pending=item.quantity - available_products,
                    expected_by=sales_order.due_date,
                    status=BackorderStatus.WAITING,
                )
                await self.backorder_service.create(db, payload)
                is_confirmed = False

        async with db_transaction(db, module="Sales Order", action="operation"):
            await db.flush()
        return is_confirmed

    async def _process_fulfill_items(
        self,
        db: AsyncSession,
        so_record: SalesOrder,
        items_to_fulfill: dict[int, int],
        actor_org_id: int,
    ) -> bool:
        """
        Process the fulfillment of goods against an active sales order.

        Translates reserved stock into permanent deductions via the InventoryService.
        Consumes stock systematically across available batches if not explicitly targeted.

        Args:
            db: Active DB session.
            so_record: The current SalesOrder entity.
            items_to_fulfill: Dictionary mapping product ID to quantity fulfilled.
            actor_org_id: Organization ID of the acting user.

        Returns:
            True if the entire order is fully fulfilled, False if partially fulfilled.

        Raises:
            AppException: If over-fulfilling or insufficient physical stock.
        """
        from app.constants.inventory_enum import InventoryTransactionType

        valid_product_ids = {item.product_id for item in so_record.items}
        invalid_product_ids = set(items_to_fulfill.keys()) - valid_product_ids

        if invalid_product_ids:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=SalesOrderMessages.INVALID_PRODUCTS.format(
                    invalid_product_ids=invalid_product_ids
                ),
            )
        all_fully_fulfilled = True

        for item in so_record.items:
            amount_to_fulfill = items_to_fulfill.get(item.product_id, 0)
            if amount_to_fulfill > 0:
                remaining = item.quantity - item.fulfilled_quantity
                if amount_to_fulfill > remaining:
                    raise AppException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=SalesOrderMessages.OVER_FULFILL.format(
                            amount_to_fulfill=amount_to_fulfill,
                            product_id=item.product_id,
                            remaining=remaining,
                        ),
                    )

                # Consume reserved quantity and actual stock
                # We do this by adjusting stock with delta_quantity = -amount_to_fulfill
                item.fulfilled_quantity += amount_to_fulfill

                if item.batch_number and item.batch_number != "ANY":
                    await self.inventory_service.adjust_stock(
                        db=db,
                        warehouse_id=so_record.source_warehouse_id,
                        product_id=item.product_id,
                        batch_number=item.batch_number,
                        delta_quantity=-amount_to_fulfill,
                        transaction_type=InventoryTransactionType.SALE,
                        actor_org_id=actor_org_id,
                        actor_id=so_record.created_by,
                        unit_cost_snapshot=item.unit_price,
                        reference_type="sales_order",
                        reference_id=so_record.id,
                        remarks="Fulfilled goods for Sales Order.",
                    )
                    await self.inventory_service.release_reserved_quantity(
                        db,
                        item.product_id,
                        so_record.source_warehouse_id,
                        amount_to_fulfill,
                    )
                else:
                    inventories_list = await self.inventory_service._get_warehouse_inventory_by_product(
                        db, item.product_id, so_record.source_warehouse_id
                    )
                    qty_to_deduct = amount_to_fulfill
                    for inv in inventories_list:
                        if qty_to_deduct <= 0:
                            break
                        if inv.quantity > 0:
                            deduct = min(inv.quantity, qty_to_deduct)
                            await self.inventory_service.adjust_stock(
                                db=db,
                                warehouse_id=so_record.source_warehouse_id,
                                product_id=item.product_id,
                                batch_number=inv.batch_number,
                                delta_quantity=-deduct,
                                transaction_type=InventoryTransactionType.SALE,
                                actor_org_id=actor_org_id,
                                actor_id=so_record.created_by,
                                unit_cost_snapshot=item.unit_price,
                                reference_type="sales_order",
                                reference_id=so_record.id,
                                remarks="Fulfilled goods for Sales Order.",
                            )
                            qty_to_deduct -= deduct

                    if qty_to_deduct > 0:
                        raise AppException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message=SalesOrderMessages.NOT_ENOUGH_STOCK.format(
                                amount_to_fulfill=amount_to_fulfill,
                                product_id=item.product_id,
                            ),
                        )

                    await self.inventory_service.release_reserved_quantity(
                        db,
                        item.product_id,
                        so_record.source_warehouse_id,
                        amount_to_fulfill,
                    )

            if item.fulfilled_quantity < item.quantity:
                all_fully_fulfilled = False

        return all_fully_fulfilled

    @log_timing
    async def fulfill_order(
        self, db: AsyncSession, so_id: int, org_id: int
    ) -> SalesOrderResponse:
        """
        Fully fulfill a sales order, consuming all remaining unfulfilled items.

        Args:
            db (AsyncSession): Active DB session.
            so_id (int): The ID of the sales order.
            org_id (int): The organization ID of the requesting user.

        Returns:
            SalesOrderResponse: The fulfilled sales order.
        """
        so_order = await self._get(db, so_id, org_id)

        if so_order.status == SalesOrderStatus.FULFILLED.value:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=SalesOrderMessages.ALREADY_FULFILLED,
            )

        if so_order.status not in (
            SalesOrderStatus.CONFIRMED.value,
            SalesOrderStatus.PARTIALLY_FULFILLED.value,
        ):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=SalesOrderMessages.INVALID_FULFILL_STATUS,
            )

        items_to_fulfill = {
            item.product_id: item.quantity - item.fulfilled_quantity
            for item in so_order.items
            if item.quantity > item.fulfilled_quantity
        }

        if not items_to_fulfill:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=SalesOrderMessages.ALL_ITEMS_FULFILLED,
            )

        await self._process_fulfill_items(db, so_order, items_to_fulfill, org_id)

        so_order.status = SalesOrderStatus.FULFILLED.value

        async with db_transaction(db, module="Sales Order", action="operation"):
            await db.flush()
            await db.refresh(so_order)
        return SalesOrderResponse.model_validate(so_order)

    @log_timing
    async def partially_fulfill_order(
        self,
        db: AsyncSession,
        so_id: int,
        payload: "PartiallyFulfillPayload",
        org_id: int,
    ) -> SalesOrderResponse:
        """
        Partially fulfill a sales order by explicitly stating the quantities fulfilled.

        Args:
            db (AsyncSession): Active DB session.
            so_id (int): The ID of the sales order.
            payload (PartiallyFulfillPayload): Specific product quantities being fulfilled.
            org_id (int): The organization ID of the requesting user.

        Returns:
            SalesOrderResponse: The updated sales order reflecting the partial fulfillment.
        """
        so_order = await self._get(db, so_id, org_id)

        if so_order.status not in (
            SalesOrderStatus.CONFIRMED.value,
            SalesOrderStatus.PARTIALLY_FULFILLED.value,
        ):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=SalesOrderMessages.PARTIAL_FULFILL_INVALID_STATUS,
            )

        items_to_fulfill = {item.product_id: item.quantity for item in payload.items}

        is_fully_fulfilled = await self._process_fulfill_items(
            db, so_order, items_to_fulfill, org_id
        )

        so_order.status = (
            SalesOrderStatus.FULFILLED.value
            if is_fully_fulfilled
            else SalesOrderStatus.PARTIALLY_FULFILLED.value
        )

        async with db_transaction(db, module="Sales Order", action="operation"):
            await db.flush()
            await db.refresh(so_order)
        return SalesOrderResponse.model_validate(so_order)
