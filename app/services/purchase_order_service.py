"""
Purchase order service for managing procurement lifecycles.

Coordinates the creation, approval, and receipt (full or partial) of purchase orders.
Integrates tightly with the InventoryService to accurately reflect received stock.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.constants.purchase_order_enum import PurchaseOrderStatus, PurchaseOrderMessages
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.purchase_order import (
    PurchaseOrderCreateInternal,
    PurchaseOrderUpdate,
    PurchaseOrderStatusUpdate,
    PurchaseOrderItemsUpdate,
    PartiallyReceivePayload,
)
from app.db.models.purchase_order import PurchaseOrder
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing
from app.services.purchase_order_item_service import PurchaseOrderItemService
from app.schemas.purchase_order import (
    PurchaseOrderItemCreateInternal,
    PurchaseOrderResponse,
)
from app.services.inventory_service import InventoryService
from app.constants.inventory_enum import InventoryTransactionType
from app.constants.purchase_order_enum import po_allowed_transitions


class PurchaseOrderService:
    """
    Service layer driving data validation and business rules for Purchase Orders.
    """

    def __init__(
        self,
        repo: PurchaseOrderRepository,
        warehouse_repo: WarehouseRepository,
        supplier_repo: SupplierRepository,
        poi_service: PurchaseOrderItemService,
        inventory_service: InventoryService,
    ) -> None:
        """
        Initialize the PurchaseOrderService with necessary dependencies.

        Args:
            repo: Data access layer for purchase orders.
            warehouse_repo: Used to validate destination warehouse ownership.
            supplier_repo: Used to validate supplier ownership.
            poi_service: Service to manage line items within the order.
            inventory_service: Service to adjust stock levels upon receipt.
        """
        self.repo = repo
        self.warehouse_repo = warehouse_repo
        self.supplier_repo = supplier_repo
        self.poi_service = poi_service
        self.inventory_service = inventory_service

    def _generate_po_number(self) -> str:
        """Generate a unique human-readable Purchase Order number."""
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"PO-{now_str}-{short_uuid}"

    @log_timing
    async def _create(
        self, db: AsyncSession, payload: PurchaseOrderCreateInternal
    ) -> PurchaseOrder:
        """
        Create a new draft purchase order directly in the database.

        Args:
            db: Active DB session.
            payload: Validated PO creation details.

        Returns:
            The created PurchaseOrder entity.

        Raises:
            AppException: If warehouse/supplier missing or cross-tenant violations.
        """
        # Validate Warehouse exists and belongs to the actor's organization
        warehouse = await self.warehouse_repo.get_by_id(
            db, payload.destination_warehouse_id
        )
        if not warehouse or warehouse.organization_id != payload.actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate Supplier exists and belongs to the actor's organization
        supplier = await self.supplier_repo.get_by_id(db, payload.supplier_id)
        if not supplier or supplier.organization_id != payload.actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Supplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Generate unique PO number
        po_number = self._generate_po_number()

        po_record = PurchaseOrder(
            supplier_id=payload.supplier_id,
            destination_warehouse_id=payload.destination_warehouse_id,
            po_number=po_number,
            status=payload.status,
            created_by=payload.created_by,
        )

        try:
            await self.repo.create(db, po_record)
            await db.flush()
            await db.refresh(po_record)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Purchase Order"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Purchase Order", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        po_items = PurchaseOrderItemCreateInternal(
            po_id=po_record.id, supplier_id=payload.supplier_id, items=payload.items
        )
        print(po_items)
        print("*" * 100)

        await self.poi_service.create(db, po_items)

        await db.flush()
        await db.refresh(po_record, ["items"])

        return po_record

    @log_timing
    async def create(
        self, db: AsyncSession, payload: PurchaseOrderCreateInternal
    ) -> PurchaseOrderResponse:
        """
        Creates a new draft purchase order.
        """
        record = await self._create(db, payload)
        return PurchaseOrderResponse.model_validate(record)

    @log_timing
    async def get_by_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[list[PurchaseOrderResponse], int]:
        """
        Retrieve all purchase orders associated with a specific warehouse.

        Args:
            db: Active DB session.
            warehouse_id: Target warehouse.
            actor_org_id: Organization ID of the requesting user.
            params: Pagination filters.

        Returns:
            A tuple of PO schemas and total count.
        """
        warehouse = await self.warehouse_repo.get_by_id(db, warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        records, total = await self.repo.get_all_by_warehouse(db, warehouse_id, params)
        return [PurchaseOrderResponse.model_validate(r) for r in records], total

    @log_timing
    async def _get(
        self, db: AsyncSession, po_id: int, actor_org_id: int
    ) -> PurchaseOrder:
        # internal get
        """
        Retrieves a purchase order by ID and ensures tenant isolation.
        """
        record = await self.repo.get_by_id(db, po_id)
        if not record:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Purchase Order"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate ownership via the linked warehouse
        warehouse = await self.warehouse_repo.get_by_id(
            db, record.destination_warehouse_id
        )
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Purchase Order"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return record

    @log_timing
    async def update(
        self,
        db: AsyncSession,
        po_id: int,
        payload: PurchaseOrderUpdate,
        actor_org_id: int,
    ) -> PurchaseOrderResponse:
        """
        Updates basic fields of a purchase order (only if it's in draft status).
        """
        record = await self._get(db, po_id, actor_org_id)

        if record.status != PurchaseOrderStatus.DRAFT:
            raise AppException(
                message=PurchaseOrderMessages.NOT_DRAFT_UPDATE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        update_data = payload.model_dump(exclude_unset=True)

        # If supplier or warehouse changed, validate them
        if (
            "destination_warehouse_id" in update_data
            and update_data["destination_warehouse_id"]
            != record.destination_warehouse_id
        ):
            warehouse = await self.warehouse_repo.get_by_id(
                db, update_data["destination_warehouse_id"]
            )
            if not warehouse or warehouse.organization_id != actor_org_id:
                raise AppException(
                    message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        if (
            "supplier_id" in update_data
            and update_data["supplier_id"] != record.supplier_id
        ):
            supplier = await self.supplier_repo.get_by_id(
                db, update_data["supplier_id"]
            )
            if not supplier or supplier.organization_id != actor_org_id:
                raise AppException(
                    message=CrudMessages.NOT_FOUND.format(module="Supplier"),
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        for field, value in update_data.items():
            setattr(record, field, value)

        try:
            await db.flush()
            await db.refresh(record)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Purchase Order"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Purchase Order", action="update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return record

    @log_timing
    async def get(
        self, db: AsyncSession, po_id: int, actor_org_id: int
    ) -> PurchaseOrderResponse:
        """
        Retrieves a purchase order by ID and ensures tenant isolation.
        """
        record = await self._get(db, po_id, actor_org_id)
        return PurchaseOrderResponse.model_validate(record)

    @log_timing
    async def update_status(
        self,
        db: AsyncSession,
        po_id: int,
        payload: PurchaseOrderStatusUpdate,
        actor_id: int,
        actor_org_id: int,
    ) -> PurchaseOrderResponse:
        """
        Updates the status of a purchase order.
        Special handling for approval.
        """
        record = await self._get(db, po_id, actor_org_id)

        if payload.status not in po_allowed_transitions.get(record.status):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Can not change status from {record.status} to {payload.status.value}.",
            )

        record.status = payload.status.value
        if record.status == PurchaseOrderStatus.APPROVED.value:
            record.approved_by = actor_id
            record.approved_at = datetime.now(timezone.utc)

        try:
            await db.flush()
            await db.refresh(record)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Purchase Order"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            import traceback

            traceback.print_exc()
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Purchase Order", action="status update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return PurchaseOrderResponse.model_validate(record)

    @log_timing
    async def delete(self, db: AsyncSession, po_id: int, actor_org_id: int) -> None:
        """
        Deletes a purchase order (only allowed if it's a draft).
        """
        record = await self._get(db, po_id, actor_org_id)

        if record.status != PurchaseOrderStatus.DRAFT:
            raise AppException(
                message=PurchaseOrderMessages.NOT_DRAFT_DELETE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            await self.repo.delete(db, record)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_RELATIONAL_CONSTRAINT.format(
                    module="Purchase Order"
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Purchase Order", action="deletion"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @log_timing
    async def update_order_items(
        self,
        db: AsyncSession,
        po_id: int,
        payload: PurchaseOrderItemsUpdate,
        actor_role: str,
        actor_org_id: int,
    ) -> None:
        """
        Updates the items of an existing purchase order, subject to state-machine constraints.
        """
        record = await self._get(db, po_id, actor_org_id)

        # Check state machine and role constraints
        if record.status == PurchaseOrderStatus.DRAFT:
            pass  # Anyone with org access can edit draft items
        elif record.status == PurchaseOrderStatus.PENDING_APPROVAL:
            from app.constants.user_enum import UserRole

            if actor_role != UserRole.WAREHOUSE_MANAGER.value:
                raise AppException(
                    message=PurchaseOrderMessages.PENDING_APPROVAL_UNAUTHORIZED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        else:
            raise AppException(
                message=PurchaseOrderMessages.UPDATE_INVALID_STATUS.format(
                    status=record.status
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Update the items
        poi_payload = PurchaseOrderItemCreateInternal(
            po_id=record.id, supplier_id=record.supplier_id, items=payload.items
        )

        await self.poi_service.update_items(db, poi_payload)

    async def _process_receive_items(
        self,
        db: AsyncSession,
        po_record: PurchaseOrder,
        items_to_receive: dict[int, int],
        actor_org_id: int,
    ) -> bool:
        """
        Process the receiving of physical goods against an active purchase order.

        Updates the line item received quantities and delegates to InventoryService
        to mutate physical stock limits and log transactions.

        Args:
            db: Active DB session.
            po_record: The current PurchaseOrder entity.
            items_to_receive: Dictionary mapping product ID to quantity received.
            actor_org_id: Organization ID of the acting user.

        Returns:
            True if the entire order is now fully received, False if partial.

        Raises:
            AppException: If over-receiving or supplying invalid products.
        """

        valid_product_ids = {item.product_id for item in po_record.items}
        invalid_product_ids = set(items_to_receive.keys()) - valid_product_ids

        if invalid_product_ids:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=PurchaseOrderMessages.INVALID_PRODUCTS.format(
                    invalid_product_ids=invalid_product_ids
                ),
            )
        all_fully_received = True

        for item in po_record.items:
            amount_to_receive = items_to_receive.get(item.product_id, 0)
            if amount_to_receive > 0:
                # Prevent receiving more than ordered
                remaining = item.quantity - item.received_quantity
                if amount_to_receive > remaining:
                    raise AppException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=PurchaseOrderMessages.OVER_RECEIVE.format(
                            amount_to_receive=amount_to_receive,
                            product_id=item.product_id,
                            remaining=remaining,
                        ),
                    )

                # Update item received quantity
                item.received_quantity += amount_to_receive

                # Safely adjust physical stock and log ledger transaction
                await self.inventory_service.adjust_stock(
                    db=db,
                    warehouse_id=po_record.destination_warehouse_id,
                    product_id=item.product_id,
                    batch_number=po_record.po_number,
                    delta_quantity=amount_to_receive,
                    transaction_type=InventoryTransactionType.PURCHASE,
                    actor_org_id=actor_org_id,
                    actor_id=po_record.created_by,
                    unit_cost_snapshot=item.unit_price,
                    reference_type="purchase_order",
                    reference_id=po_record.id,
                    remarks="Received goods for Purchase Order.",
                )

            if item.received_quantity < item.quantity:
                all_fully_received = False

        return all_fully_received

    @log_timing
    async def received_order(
        self, db: AsyncSession, po_id: int, role: str, org_id: int
    ) -> PurchaseOrderResponse:
        """
        Mark a purchase order as completely received in a single action.

        Calculates remaining unreceived quantities and processes them.

        Args:
            db: Active DB session.
            po_id: ID of the purchase order.
            role: Role of the acting user.
            org_id: Organization ID of the acting user.

        Returns:
            The fully received PO schema.

        Raises:
            AppException: If already received or in invalid state.
        """
        po_order = await self._get(db, po_id, org_id)

        if po_order.status == PurchaseOrderStatus.RECEIVED.value:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=PurchaseOrderMessages.ALREADY_RECEIVED,
            )

        if po_order.status not in (
            PurchaseOrderStatus.APPROVED.value,
            PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
        ):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=PurchaseOrderMessages.INVALID_RECEIVE_STATUS,
            )

        items_to_receive = {
            item.product_id: item.quantity - item.received_quantity
            for item in po_order.items
            if item.quantity > item.received_quantity
        }

        if not items_to_receive:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=PurchaseOrderMessages.ALL_ITEMS_RECEIVED,
            )

        await self._process_receive_items(db, po_order, items_to_receive, org_id)

        po_order.status = PurchaseOrderStatus.RECEIVED.value

        try:
            await db.flush()
            await db.refresh(po_order)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Purchase Order"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            import traceback

            traceback.print_exc()
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Purchase Order", action="status update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return PurchaseOrderResponse.model_validate(po_order)

    @log_timing
    async def partially_received_order(
        self,
        db: AsyncSession,
        po_id: int,
        payload: PartiallyReceivePayload,
        role: str,
        org_id: int,
    ) -> PurchaseOrderResponse:
        """
        Record a partial receipt of goods for a purchase order.

        Args:
            db: Active DB session.
            po_id: ID of the purchase order.
            payload: Quantities received for specific line items.
            role: Role of the acting user.
            org_id: Organization ID of the acting user.

        Returns:
            The updated PO schema, reflecting partial or full receipt state.
        """
        po_order = await self._get(db, po_id, org_id)

        if po_order.status not in (
            PurchaseOrderStatus.APPROVED.value,
            PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
        ):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=PurchaseOrderMessages.PARTIAL_RECEIVE_INVALID_STATUS,
            )

        items_to_receive = {item.product_id: item.quantity for item in payload.items}

        is_fully_received = await self._process_receive_items(
            db, po_order, items_to_receive, org_id
        )

        po_order.status = (
            PurchaseOrderStatus.RECEIVED.value
            if is_fully_received
            else PurchaseOrderStatus.PARTIALLY_RECEIVED.value
        )

        try:
            await db.flush()
            await db.refresh(po_order)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Purchase Order"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            import traceback

            traceback.print_exc()
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Purchase Order", action="status update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return PurchaseOrderResponse.model_validate(po_order)
