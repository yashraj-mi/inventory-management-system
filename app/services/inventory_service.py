"""
Inventory service module managing physical stock levels.

Handles stock tracking, batch creation, quantity reservations, and stock
adjustments. Enforces validation rules ensuring stock quantities are only modified
through legitimate ledger transactions.
"""

from app.db.session_utils import db_transaction
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from datetime import date, timedelta


from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse
from app.services.inventory_transaction_service import InventoryTransactionService
from app.schemas.inventory_transaction import InventoryTransactionCreate
from app.constants.inventory_enum import InventoryTransactionType, InventoryMessages
from decimal import Decimal
from app.db.models.inventory import Inventory
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing
from app.repositories.warehouse_repository import WarehouseRepository
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.backorder_service import BackorderService


class InventoryService:
    """
    Service layer driving data validation and business rules for Inventory.
    """

    def __init__(
        self,
        repo: InventoryRepository,
        product_repo: ProductRepository,
        warehouse_repo: WarehouseRepository,
        inventory_transaction_service: InventoryTransactionService,
        backorder_service: "BackorderService",
    ) -> None:
        """
        Initialize the InventoryService with its dependent services and repositories.

        Args:
            repo: Data access layer for inventory records.
            product_repo: Data access layer to validate product ownership.
            warehouse_repo: Data access layer to validate warehouse ownership.
            inventory_transaction_service: Service to log immutable ledger movements.
            backorder_service: Service to auto-settle backorders upon stock receipt.
        """
        self.repo = repo
        self.product_repo = product_repo
        self.warehouse_repo = warehouse_repo
        self.inventory_transaction_service = inventory_transaction_service
        self.backorder_service = backorder_service

    @log_timing
    async def _create(
        self, db: AsyncSession, payload: InventoryCreate, actor_org_id: int
    ) -> Inventory:
        """
        Create a new inventory batch record directly in the database.

        Forces initial quantity to 0 to prevent ledger bypass. Sets expiry dates
        if the product is marked as perishable.

        Args:
            db: The active database session context.
            payload: Validated schema containing batch details.
            actor_org_id: The ID of the organization attempting creation.

        Returns:
            The created Inventory database entity.

        Raises:
            AppException: For cross-tenant data access, duplicate batches (409), or DB errors.
        """
        # Validate that Product exists and belongs to the actor's organization
        product = await self.product_repo.get_by_id(db, payload.product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate that Warehouse exists and belongs to the actor's organization
        warehouse = await self.warehouse_repo.get_by_id(db, payload.warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Check for existing mapping with the same batch number
        existing = await self.repo.get_by_unique_key(
            db, payload.warehouse_id, payload.product_id, payload.batch_number
        )
        if existing:
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Inventory", field="batch_number", value=payload.batch_number
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        expire_date = None
        if product.is_perishable:
            expire_date = date.today() + timedelta(days=product.shelf_life)

        inventory_record = Inventory(
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            batch_number=payload.batch_number,
            expiry_date=expire_date,
            quantity=0,  # ALWAYS force initial quantity to 0 to prevent ledger bypass
            reserved_quantity=payload.reserved_quantity,
            reorder_level=payload.reorder_level,
            status=payload.status,
        )

        async with db_transaction(db, module="Inventory", action="operation"):
            await self.repo.create(db, inventory_record)
            await db.flush()
            await db.refresh(inventory_record)
        return inventory_record

    @log_timing
    async def create(
        self, db: AsyncSession, payload: InventoryCreate, actor_org_id: int
    ) -> InventoryResponse:
        """
        Creates a new inventory batch record.
        """
        record = await self._create(db, payload, actor_org_id)
        return InventoryResponse.model_validate(record)

    @log_timing
    async def get_by_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[list[InventoryResponse], int]:
        """
        Retrieves all inventory items for a specific warehouse.
        """
        warehouse = await self.warehouse_repo.get_by_id(db, warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        records, total = await self.repo.get_all_by_warehouse(db, warehouse_id, params)
        return [InventoryResponse.model_validate(r) for r in records], total

    @log_timing
    async def get_by_product(
        self,
        db: AsyncSession,
        product_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[list[InventoryResponse], int]:
        """
        Retrieves all inventory items globally across warehouses for a specific product.
        """
        product = await self.product_repo.get_by_id(db, product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        records, total = await self.repo.get_all_by_product(db, product_id, params)
        return [InventoryResponse.model_validate(r) for r in records], total

    @log_timing
    async def _get(
        self, db: AsyncSession, inventory_id: int, actor_org_id: int
    ) -> Inventory:
        # internal get
        """
        Retrieves an inventory record by ID.
        """
        record = await self.repo.get_by_id(db, inventory_id)
        if not record:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Inventory"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate ownership via the linked product
        product = await self.product_repo.get_by_id(db, record.product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Inventory"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return record

    @log_timing
    async def get(
        self, db: AsyncSession, inventory_id: int, actor_org_id: int
    ) -> InventoryResponse:
        """
        Retrieves an inventory record by ID.
        """
        record = await self._get(db, inventory_id, actor_org_id)
        return InventoryResponse.model_validate(record)

    @log_timing
    async def update(
        self,
        db: AsyncSession,
        inventory_id: int,
        payload: InventoryUpdate,
        actor_org_id: int,
    ) -> InventoryResponse:
        """
        Updates an existing inventory record.
        """
        record = await self._get(db, inventory_id, actor_org_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "quantity" in update_data:
            raise AppException(
                message=InventoryMessages.DIRECT_UPDATE_FORBIDDEN,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent unique constraint violations if batch_number is changed
        if (
            "batch_number" in update_data
            and update_data["batch_number"] != record.batch_number
        ):
            existing = await self.repo.get_by_unique_key(
                db, record.warehouse_id, record.product_id, update_data["batch_number"]
            )
            if existing:
                raise AppException(
                    message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                        module="Inventory",
                        field="batch_number",
                        value=update_data["batch_number"],
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                )

        for field, value in update_data.items():
            setattr(record, field, value)

        async with db_transaction(db, module="Inventory", action="operation"):
            await db.flush()
            await db.refresh(record)
        return InventoryResponse.model_validate(record)

    @log_timing
    async def delete(
        self, db: AsyncSession, inventory_id: int, actor_org_id: int
    ) -> None:
        """
        Deletes an inventory record by ID.
        """
        record = await self._get(db, inventory_id, actor_org_id)

        async with db_transaction(db, module="Inventory", action="operation"):
            await self.repo.delete(db, record)
            await db.flush()

    @log_timing
    async def adjust_stock(
        self,
        db: AsyncSession,
        warehouse_id: int,
        product_id: int,
        batch_number: str,
        delta_quantity: int,
        transaction_type: InventoryTransactionType,
        actor_org_id: int,
        actor_id: int,
        unit_cost_snapshot: Decimal | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        remarks: str | None = None,
    ) -> InventoryResponse:
        """
        Adjust stock quantity securely via an immutable transaction ledger.

        This is the ONLY approved way to change stock levels. It updates the physical
        count and logs the delta simultaneously. Auto-settles backorders if stock is received.

        Args:
            db: The active database session context.
            warehouse_id: Target warehouse.
            product_id: Target product.
            batch_number: Target batch number.
            delta_quantity: The positive or negative amount to adjust.
            transaction_type: Classification of the stock movement.
            actor_org_id: Organization ID of the actor.
            actor_id: User ID of the actor.
            unit_cost_snapshot: Historical cost at the time of movement.
            reference_type: Contextual reference (e.g., 'PO', 'SO').
            reference_id: Contextual ID for traceability.
            remarks: Optional free-text notes.

        Returns:
            The updated InventoryResponse.

        Raises:
            AppException: If delta is zero, stock goes negative, or batch doesn't exist on negative deltas.
        """
        if delta_quantity == 0:
            raise AppException(
                message=InventoryMessages.ZERO_DELTA,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        existing = await self.repo.get_by_unique_key(
            db, warehouse_id, product_id, batch_number
        )

        if existing:
            # Validate subtraction doesn't go below zero
            if existing.quantity + delta_quantity < 0:
                raise AppException(
                    message=InventoryMessages.INSUFFICIENT_STOCK,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            existing.quantity += delta_quantity
            inventory_record = existing
        else:
            if delta_quantity < 0:
                raise AppException(
                    message=InventoryMessages.NON_EXISTENT_BATCH,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            # Implicitly create the batch if it doesn't exist and we are adding stock
            payload = InventoryCreate(
                warehouse_id=warehouse_id,
                product_id=product_id,
                batch_number=batch_number,
                quantity=0,  # This will be enforced to 0 by create(), which is what we want before adjusting
            )
            inventory_record = await self._create(db, payload, actor_org_id)
            inventory_record.quantity += delta_quantity

        # Log exactly one transaction
        txn_payload = InventoryTransactionCreate(
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_number=batch_number,
            transaction_type=transaction_type,
            quantity=delta_quantity,
            unit_cost_snapshot=unit_cost_snapshot,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks,
            created_by=actor_id,
        )
        await self.inventory_transaction_service.create(db, txn_payload, actor_org_id)

        if delta_quantity > 0:
            await self.backorder_service.settle_backorders(
                db, product_id, warehouse_id, actor_org_id
            )

        return InventoryResponse.model_validate(inventory_record)

    async def _get_warehouse_inventory_by_product(
        self, db: AsyncSession, product_id: int, warehouse_id: int
    ) -> list[Inventory]:
        """
        Retrieve all inventory batch entries for a specific product in a warehouse.

        Args:
            db: Active DB session.
            product_id: Product ID.
            warehouse_id: Warehouse ID.

        Returns:
            List of inventory models.
        """
        return await self.repo.get_warehouse_inventory_by_product(
            db, product_id, warehouse_id
        )

    async def get_warehouse_products(
        self, db: AsyncSession, product_id: int, warehouse_id: int
    ):
        """
        Retrieve total aggregate stock availability for a product in a warehouse.

        Args:
            db: Active DB session.
            product_id: Product ID.
            warehouse_id: Warehouse ID.

        Returns:
            Total available unreserved stock (int).
        """
        val = await self.repo.get_warehouse_product(db, product_id, warehouse_id)
        return val if val is not None else 0

    async def reserve_quantity(
        self, db: AsyncSession, product_id: int, warehouse_id: int, quantity: int
    ):
        """
        Reserves a specific quantity of a product in a warehouse.

        Iterates over available batches and increments their reserved quantity until the
        requested quantity is fully reserved.

        Args:
            db (AsyncSession): Active DB session.
            product_id (int): Product ID to reserve.
            warehouse_id (int): Warehouse ID where reservation occurs.
            quantity (int): Total quantity to reserve.
        """
        if quantity <= 0:
            return

        inventories = await self._get_warehouse_inventory_by_product(
            db, product_id, warehouse_id
        )

        for inv in inventories:
            available = inv.quantity - inv.reserved_quantity
            if available <= 0:
                continue

            if available >= quantity:
                inv.reserved_quantity += quantity
                quantity = 0
                break
            else:
                inv.reserved_quantity += available
                quantity -= available

        async with db_transaction(db, module="Inventory", action="operation"):
            await db.flush()

    async def release_reserved_quantity(
        self, db: AsyncSession, product_id: int, warehouse_id: int, quantity: int
    ):
        """
        Releases a previously reserved quantity of a product in a warehouse.

        Iterates over batches with reserved stock and decrements their reserved quantity
        until the requested quantity is fully released.

        Args:
            db (AsyncSession): Active DB session.
            product_id (int): Product ID to release.
            warehouse_id (int): Warehouse ID where release occurs.
            quantity (int): Total quantity to release.
        """
        if quantity <= 0:
            return

        inventories = await self._get_warehouse_inventory_by_product(
            db, product_id, warehouse_id
        )

        for inv in inventories:
            if quantity <= 0:
                break
            if inv.reserved_quantity > 0:
                removed = min(inv.reserved_quantity, quantity)
                inv.reserved_quantity -= removed
                quantity -= removed

        async with db_transaction(db, module="Inventory", action="operation"):
            await db.flush()
