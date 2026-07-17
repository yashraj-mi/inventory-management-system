"""Provide API endpoints for the Inventory Transactions domain.

This module defines routes for logging and retrieving inventory stock adjustments,
including queries by warehouse and product.
"""

from app.db.models.user import User
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.response import StandardResponse, PaginatedData
from app.constants.inventory_enum import InventoryTransactionMessages
from app.schemas.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionResponse,
)
from app.services.inventory_transaction_service import InventoryTransactionService
from app.dependencies.inventory_transaction import get_inventory_transaction_service
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.core.security import get_current_user
from app.dependencies.pagination import PaginationParams, get_pagination_params


router = APIRouter(prefix="/inventory-transactions", tags=["Inventory Transactions"])


@router.post(
    "/",
    response_model=StandardResponse[InventoryTransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Inventory Transaction",
    dependencies=[
        Depends(require_permission(Permissions.INVENTORY_TRANSACTION_CREATE))
    ],
)
async def create_inventory_transaction(
    payload: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    service: InventoryTransactionService = Depends(get_inventory_transaction_service),
    current_user: User = Depends(get_current_user),
):
    """Create a new inventory transaction record.

    Executes a POST request to `/inventory-transactions/` to log a stock change.

    Args:
        payload (InventoryTransactionCreate): The transaction details.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryTransactionService): The inventory transaction service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks admin or manager permissions.

    Returns:
        StandardResponse[InventoryTransactionResponse]: A standardized wrapper containing the transaction.
    """
    org_id = current_user.organization_id

    transaction_data = payload.model_dump()
    if transaction_data.get("created_by") is None:
        transaction_data["created_by"] = current_user.id

    transaction_record = await service.create(
        db, InventoryTransactionCreate(**transaction_data), org_id
    )

    return StandardResponse(
        success=True,
        message=InventoryTransactionMessages.LOGGED_SUCCESSFULLY,
        data=transaction_record,
    )


@router.get(
    "/{transaction_id}",
    response_model=StandardResponse[InventoryTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Inventory Transaction by ID",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_TRANSACTION_READ))],
)
async def get_inventory_transaction(
    transaction_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryTransactionService = Depends(get_inventory_transaction_service),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific inventory transaction by its ID.

    Executes a GET request to `/inventory-transactions/{transaction_id}` to fetch a ledger record.

    Args:
        transaction_id (int): The unique ID of the transaction.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryTransactionService): The inventory transaction service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the transaction ID is invalid.
        HTTPException (403): If the user lacks admin or manager permissions.
        HTTPException (404): If the transaction is not found.

    Returns:
        StandardResponse[InventoryTransactionResponse]: A standardized wrapper with transaction details.
    """
    org_id = current_user.organization_id
    transaction_record = await service.get(db, transaction_id, org_id)

    return StandardResponse(
        success=True,
        message=InventoryTransactionMessages.RETRIEVED_SUCCESSFULLY,
        data=transaction_record,
    )


@router.get(
    "/warehouse/{warehouse_id}",
    response_model=StandardResponse[PaginatedData[InventoryTransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Transactions by Warehouse",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_TRANSACTION_READ))],
)
async def get_transactions_by_warehouse(
    warehouse_id: int = Path(..., gt=0),
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    service: InventoryTransactionService = Depends(get_inventory_transaction_service),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a paginated list of transactions for a specific warehouse.

    Executes a GET request to `/inventory-transactions/warehouse/{warehouse_id}` to fetch ledger entries.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        params (PaginationParams): Pagination parameters (page and size).
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryTransactionService): The inventory transaction service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the warehouse ID or pagination parameters are invalid.
        HTTPException (403): If the user lacks admin or manager permissions.

    Returns:
        StandardResponse[PaginatedData[InventoryTransactionResponse]]: A paginated list of transactions.
    """
    org_id = current_user.organization_id
    items, total = await service.get_by_warehouse(db, warehouse_id, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    return StandardResponse(
        success=True,
        message=InventoryTransactionMessages.RETRIEVED_ALL_SUCCESSFULLY,
        data=PaginatedData(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=total_pages,
        ),
    )


@router.get(
    "/product/{product_id}",
    response_model=StandardResponse[PaginatedData[InventoryTransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Transactions by Product",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_TRANSACTION_READ))],
)
async def get_transactions_by_product(
    product_id: int = Path(..., gt=0),
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    service: InventoryTransactionService = Depends(get_inventory_transaction_service),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a paginated list of transactions for a specific product globally.

    Executes a GET request to `/inventory-transactions/product/{product_id}` to fetch ledger entries.

    Args:
        product_id (int): The unique ID of the product.
        params (PaginationParams): Pagination parameters (page and size).
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryTransactionService): The inventory transaction service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the product ID or pagination parameters are invalid.
        HTTPException (403): If the user lacks admin or manager permissions.

    Returns:
        StandardResponse[PaginatedData[InventoryTransactionResponse]]: A paginated list of transactions.
    """
    org_id = current_user.organization_id
    items, total = await service.get_by_product(db, product_id, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    return StandardResponse(
        success=True,
        message=InventoryTransactionMessages.RETRIEVED_ALL_SUCCESSFULLY,
        data=PaginatedData(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=total_pages,
        ),
    )
