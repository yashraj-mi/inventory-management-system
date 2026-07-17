"""Provide API endpoints for the Inventory domain.

This module defines routes for managing inventory records, stock adjustments,
and retrieving inventory aggregated by product or warehouse.
"""

from app.db.models.user import User
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    InventoryAdjustPayload,
)
from app.services.inventory_service import InventoryService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.dependencies.auth import get_current_user
from app.constants.inventory_enum import InventoryMessages
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params


from app.dependencies.inventory import get_inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "",
    response_model=StandardResponse[InventoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Inventory Record",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_CREATE))],
)
async def create_inventory(
    payload: InventoryCreate,
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[InventoryResponse]:
    """Create a new inventory record for a product in a warehouse.

    Executes a POST request to `/inventory` to register a new stock entity.

    Args:
        payload (InventoryCreate): The inventory payload detailing product and initial quantity.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks proper permissions.
        HTTPException (404): If the warehouse or product is not found.

    Returns:
        StandardResponse[InventoryResponse]: A standardized wrapper containing the inventory record.
    """
    org_id = current_user.organization_id
    response_data = await service.create(db, payload, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Inventory"),
        data=response_data,
    )


@router.post(
    "/{inventory_id}/adjust",
    response_model=StandardResponse[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Adjust Inventory Stock",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_CREATE))],
)
async def adjust_inventory_stock(
    payload: InventoryAdjustPayload,
    inventory_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[InventoryResponse]:
    """Adjust the stock level of an inventory record manually.

    Executes a POST request to `/inventory/{inventory_id}/adjust` to increase or decrease
    stock (e.g. for loss, damage, correction), logging an immutable ledger transaction.

    Args:
        payload (InventoryAdjustPayload): The adjustment details (delta quantity, type, remarks).
        inventory_id (int): The unique ID of the inventory record to adjust.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the adjustment results in negative stock.
        HTTPException (403): If the user lacks proper permissions.
        HTTPException (404): If the inventory record does not exist.

    Returns:
        StandardResponse[InventoryResponse]: A standardized wrapper with the updated inventory record.
    """
    org_id = current_user.organization_id
    actor_id = str(current_user.id)

    # We need the inventory record first to get the warehouse and product details
    record = await service.get(db, inventory_id, org_id)

    response_data = await service.adjust_stock(
        db=db,
        warehouse_id=record.warehouse_id,
        product_id=record.product_id,
        batch_number=record.batch_number,
        delta_quantity=payload.delta_quantity,
        transaction_type=payload.transaction_type,
        actor_org_id=org_id,
        actor_id=actor_id,
        remarks=payload.remarks,
    )

    return StandardResponse(
        success=True,
        message=InventoryMessages.ADJUSTED_SUCCESSFULLY,
        data=response_data,
    )


@router.get(
    "/warehouses/{warehouse_id}",
    response_model=StandardResponse[PaginatedData[InventoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Inventory in a Warehouse",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_READ))],
)
async def list_by_warehouse(
    warehouse_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[InventoryResponse]]:
    """Retrieve a paginated list of all inventory records inside a specific warehouse.

    Executes a GET request to `/inventory/warehouses/{warehouse_id}` to fetch stocks.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (400): If the pagination parameters or warehouse ID are invalid.
        HTTPException (403): If the user lacks access to the warehouse.

    Returns:
        StandardResponse[PaginatedData[InventoryResponse]]: A paginated list of inventory stocks.
    """
    org_id = current_user.organization_id
    records, total = await service.get_by_warehouse(db, warehouse_id, org_id, params)

    total_pages = (total + params.size - 1) // params.size

    paginated = PaginatedData(
        items=records,
        total=total,
        page=params.page,
        size=params.size,
        pages=total_pages,
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Inventory"),
        data=paginated,
    )


@router.get(
    "/products/{product_id}",
    response_model=StandardResponse[PaginatedData[InventoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Inventory globally for a Product",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_READ))],
)
async def list_by_product(
    product_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[InventoryResponse]]:
    """Retrieve a paginated list of all inventory records globally for a specific product.

    Executes a GET request to `/inventory/products/{product_id}` to fetch product stocks across warehouses.

    Args:
        product_id (int): The unique ID of the product.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (400): If the pagination parameters or product ID are invalid.
        HTTPException (403): If the user lacks proper organization access.

    Returns:
        StandardResponse[PaginatedData[InventoryResponse]]: A paginated list of inventory stocks.
    """
    org_id = current_user.organization_id
    records, total = await service.get_by_product(db, product_id, org_id, params)

    total_pages = (total + params.size - 1) // params.size

    paginated = PaginatedData(
        items=records,
        total=total,
        page=params.page,
        size=params.size,
        pages=total_pages,
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Inventory"),
        data=paginated,
    )


@router.get(
    "/{inventory_id}",
    response_model=StandardResponse[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get an Inventory Record",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_READ))],
)
async def get_inventory(
    inventory_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[InventoryResponse]:
    """Retrieve a specific inventory record by ID.

    Executes a GET request to `/inventory/{inventory_id}` to fetch an inventory record.

    Args:
        inventory_id (int): The unique ID of the inventory record.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the inventory ID is invalid.
        HTTPException (403): If the user lacks proper organization access.
        HTTPException (404): If the inventory record is not found.

    Returns:
        StandardResponse[InventoryResponse]: A standardized wrapper containing the inventory details.
    """
    org_id = current_user.organization_id
    response_data = await service.get(db, inventory_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Inventory"),
        data=response_data,
    )


@router.patch(
    "/{inventory_id}",
    response_model=StandardResponse[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Update an Inventory Record",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_UPDATE))],
)
async def update_inventory(
    payload: InventoryUpdate,
    inventory_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[InventoryResponse]:
    """Update specific attributes of an inventory record.

    Executes a PATCH request to `/inventory/{inventory_id}` to modify inventory details.

    Args:
        payload (InventoryUpdate): The payload containing attributes to update.
        inventory_id (int): The unique ID of the inventory record.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks access to the record.
        HTTPException (404): If the inventory record does not exist.

    Returns:
        StandardResponse[InventoryResponse]: A standardized wrapper with the updated inventory details.
    """
    org_id = current_user.organization_id
    response_data = await service.update(db, inventory_id, payload, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Inventory"),
        data=response_data,
    )


@router.delete(
    "/{inventory_id}",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete an Inventory Record",
    dependencies=[Depends(require_permission(Permissions.INVENTORY_DELETE))],
)
async def delete_inventory(
    inventory_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[None]:
    """Permanently delete an inventory record.

    Executes a DELETE request to `/inventory/{inventory_id}` to remove a record.

    Args:
        inventory_id (int): The unique ID of the inventory record to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (InventoryService): The inventory service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the inventory ID is invalid.
        HTTPException (403): If the user lacks access to delete the record.
        HTTPException (404): If the inventory record does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    org_id = current_user.organization_id
    await service.delete(db, inventory_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Inventory"),
        data=None,
    )
