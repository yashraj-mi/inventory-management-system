"""
Inventory transaction service for the ledger system.

Handles the logging of all physical stock movements to ensure an immutable
audit trail of adjustments, sales, and receipts.
"""

from app.db.session_utils import db_transaction
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.repositories.inventory_transaction_repository import (
    InventoryTransactionRepository,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionResponse,
)
from app.db.models.inventory_transaction import InventoryTransaction
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing


class InventoryTransactionService:
    """
    Service layer driving data validation and business rules for Inventory Transactions.
    """

    def __init__(
        self,
        repo: InventoryTransactionRepository,
        product_repo: ProductRepository,
        warehouse_repo: WarehouseRepository,
    ) -> None:
        """
        Initialize the InventoryTransactionService with necessary repositories.

        Args:
            repo: Data access layer for inventory transaction logs.
            product_repo: Data access layer to validate product ownership.
            warehouse_repo: Data access layer to validate warehouse ownership.
        """
        self.repo = repo
        self.product_repo = product_repo
        self.warehouse_repo = warehouse_repo

    @log_timing
    async def _create(
        self, db: AsyncSession, payload: InventoryTransactionCreate, actor_org_id: int
    ) -> InventoryTransaction:
        """
        Log a new immutable inventory transaction record.

        Validates product and warehouse ownership before persisting the event.

        Args:
            db: The active database session context.
            payload: Validated schema containing transaction details.
            actor_org_id: The ID of the organization acting on the transaction.

        Returns:
            The created InventoryTransaction entity.

        Raises:
            AppException: For cross-tenant data access or database persistence errors.
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

        transaction_record = InventoryTransaction(
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            batch_number=payload.batch_number,
            transaction_type=payload.transaction_type.value,
            quantity=payload.quantity,
            unit_cost_snapshot=payload.unit_cost_snapshot,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
            created_by=payload.created_by,
        )

        async with db_transaction(
            db, module="Inventory Transaction", action="operation"
        ):
            await self.repo.create(db, transaction_record)
            await db.flush()
            await db.refresh(transaction_record)
        return transaction_record

    @log_timing
    async def create(
        self, db: AsyncSession, payload: InventoryTransactionCreate, actor_org_id: int
    ) -> InventoryTransactionResponse:
        """
        Log a new inventory transaction and return its public response model.

        Args:
            db: The active database session context.
            payload: Validated schema containing transaction details.
            actor_org_id: The organization ID.

        Returns:
            The validated InventoryTransactionResponse schema.
        """
        record = await self._create(db, payload, actor_org_id)
        return InventoryTransactionResponse.model_validate(record)

    @log_timing
    async def get_by_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[list[InventoryTransactionResponse], int]:
        """
        Retrieves all transactions for a specific warehouse.
        """
        warehouse = await self.warehouse_repo.get_by_id(db, warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        records, total = await self.repo.get_all_by_warehouse(db, warehouse_id, params)
        return [InventoryTransactionResponse.model_validate(r) for r in records], total

    @log_timing
    async def get_by_product(
        self,
        db: AsyncSession,
        product_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[list[InventoryTransactionResponse], int]:
        """
        Retrieves all transactions for a specific product globally.
        """
        product = await self.product_repo.get_by_id(db, product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        records, total = await self.repo.get_all_by_product(db, product_id, params)
        return [InventoryTransactionResponse.model_validate(r) for r in records], total

    @log_timing
    async def _get(
        self, db: AsyncSession, transaction_id: int, actor_org_id: int
    ) -> InventoryTransaction:
        # internal get
        """
        Retrieves a transaction record by ID.
        """
        record = await self.repo.get_by_id(db, transaction_id)
        if not record:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Inventory Transaction"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate ownership via the linked product
        product = await self.product_repo.get_by_id(db, record.product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Inventory Transaction"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return record

    @log_timing
    async def get(
        self, db: AsyncSession, transaction_id: int, actor_org_id: int
    ) -> InventoryTransactionResponse:
        """
        Retrieves a transaction record by ID.
        """
        record = await self._get(db, transaction_id, actor_org_id)
        return InventoryTransactionResponse.model_validate(record)
