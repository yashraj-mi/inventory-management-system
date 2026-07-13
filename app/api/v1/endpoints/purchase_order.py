"""Provide API endpoints for the Purchase Order domain.

This module defines routes for creating, managing, and tracking purchase orders,
including lifecycle transitions and receiving workflows.
"""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderCreateInternal,
    PurchaseOrderUpdate,
    PurchaseOrderStatusUpdate,
    PurchaseOrderResponse,
    PurchaseOrderItemsUpdate,
    PartiallyReceivePayload,
)
from app.constants.purchase_order_enum import PurchaseOrderMessages
from app.services.purchase_order_service import PurchaseOrderService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.auth import ALLOW_COMMON_ORG, ALLOW_ADMIN_OR_MANAGER
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params


from app.dependencies.purchase_order import get_purchase_order_service as get_po_service

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post(
    "",
    response_model=StandardResponse[PurchaseOrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a Draft Purchase Order",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[PurchaseOrderResponse]:
    """Create a new draft purchase order in a specific warehouse.

    Executes a POST request to `/purchase-orders` to initialize a PO.

    Args:
        payload (PurchaseOrderCreate): The purchase order details.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks permissions.

    Returns:
        StandardResponse[PurchaseOrderResponse]: A standardized wrapper containing the PO.
    """
    print()
    org_id = current_user.get("org_id")
    user_id = current_user.get("sub")

    # We dynamically attach internal requirements missing from the user payload.
    internal_payload = PurchaseOrderCreateInternal(
        **payload.model_dump(),
        po_number="",  # the service generates this
        created_by=int(user_id),
        actor_org_id=int(org_id),
    )

    response_data = await service.create(db, internal_payload)

    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Purchase Order"),
        data=response_data,
    )


@router.get(
    "/warehouses/{warehouse_id}",
    response_model=StandardResponse[PaginatedData[PurchaseOrderResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Purchase Orders for a Warehouse",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def list_by_warehouse(
    warehouse_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[PurchaseOrderResponse]]:
    """Retrieve a paginated list of all purchase orders sent to a specific warehouse.

    Executes a GET request to `/purchase-orders/warehouses/{warehouse_id}`.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters.

    Raises:
        HTTPException (400): If pagination or warehouse ID are invalid.
        HTTPException (403): If the user lacks access to the warehouse.

    Returns:
        StandardResponse[PaginatedData[PurchaseOrderResponse]]: A paginated list of POs.
    """
    org_id = current_user.get("org_id")
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
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Purchase Order"),
        data=paginated,
    )


@router.get(
    "/{po_id}",
    response_model=StandardResponse[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a Purchase Order",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def get_purchase_order(
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[PurchaseOrderResponse]:
    """Retrieve a specific purchase order by ID.

    Executes a GET request to `/purchase-orders/{po_id}` to fetch a PO.

    Args:
        po_id (int): The unique ID of the PO.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the PO ID is invalid.
        HTTPException (403): If the user lacks access to the PO.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[PurchaseOrderResponse]: A standardized wrapper containing the PO details.
    """
    org_id = current_user.get("org_id")
    response_data = await service.get(db, po_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Purchase Order"),
        data=response_data,
    )


@router.patch(
    "/{po_id}",
    response_model=StandardResponse[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a Draft Purchase Order",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def update_purchase_order(
    payload: PurchaseOrderUpdate,
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[PurchaseOrderResponse]:
    """Update details of a draft purchase order.

    Executes a PATCH request to `/purchase-orders/{po_id}` to update supplier or destination.
    Only drafts can be updated.

    Args:
        payload (PurchaseOrderUpdate): The fields to update.
        po_id (int): The unique ID of the PO.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid or PO is not in draft.
        HTTPException (403): If the user lacks access to the PO.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[PurchaseOrderResponse]: A standardized wrapper with the updated PO.
    """
    org_id = current_user.get("org_id")
    response_data = await service.update(db, po_id, payload, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Purchase Order"),
        data=response_data,
    )


@router.patch(
    "/{po_id}/status",
    response_model=StandardResponse[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Purchase Order Status",
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def update_purchase_order_status(
    payload: PurchaseOrderStatusUpdate,
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[PurchaseOrderResponse]:
    """Progress the lifecycle status of a purchase order.

    Executes a PATCH request to `/purchase-orders/{po_id}/status` to approve, order, or cancel.

    Args:
        payload (PurchaseOrderStatusUpdate): The new status payload.
        po_id (int): The unique ID of the PO.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the transition is invalid.
        HTTPException (403): If the user lacks Manager or Admin privileges.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[PurchaseOrderResponse]: A standardized wrapper with the updated PO.
    """
    org_id = current_user.get("org_id")
    user_id = int(current_user.get("sub"))
    response_data = await service.update_status(db, po_id, payload, user_id, org_id)

    return StandardResponse(
        success=True,
        message=PurchaseOrderMessages.STATUS_UPDATED,
        data=response_data,
    )


@router.delete(
    "/{po_id}",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a Draft Purchase Order",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def delete_purchase_order(
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[None]:
    """Permanently delete a draft purchase order.

    Executes a DELETE request to `/purchase-orders/{po_id}`.

    Args:
        po_id (int): The unique ID of the PO to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the PO is not in Draft status.
        HTTPException (403): If the user lacks access to delete the PO.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    org_id = current_user.get("org_id")
    await service.delete(db, po_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Purchase Order"),
        data=None,
    )


@router.put(
    "/{po_id}/items",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Update Purchase Order Items",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def update_purchase_order_items(
    payload: PurchaseOrderItemsUpdate,
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[None]:
    """Replace the items of a purchase order.

    Executes a PUT request to `/purchase-orders/{po_id}/items` to modify order contents.
    Allowed only in Draft status (for org users), or Pending Approval (for Warehouse Managers).

    Args:
        payload (PurchaseOrderItemsUpdate): The list of items to set.
        po_id (int): The unique ID of the PO.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the PO status prohibits updates.
        HTTPException (403): If the user lacks appropriate permissions.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating success.
    """
    org_id = current_user.get("org_id")
    role = current_user.get("role")

    await service.update_order_items(db, po_id, payload, role, org_id)

    return StandardResponse(
        success=True,
        message=PurchaseOrderMessages.ITEMS_UPDATED,
        data=None,
    )


@router.patch(
    "/{po_id}/received",
    response_model=StandardResponse[PurchaseOrderResponse],
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def purchase_order_received(
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
):
    """Mark a purchase order as fully received.

    Executes a PATCH request to `/purchase-orders/{po_id}/received` to update inventory.

    Args:
        po_id (int): The unique ID of the PO.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the PO cannot be received.
        HTTPException (403): If the user lacks Admin or Manager privileges.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[PurchaseOrderResponse]: A standardized wrapper with the updated PO.
    """
    org_id = current_user.get("org_id")
    role = current_user.get("role")

    po_order = await service.received_order(db, po_id, role, org_id)
    return StandardResponse(
        message=PurchaseOrderMessages.RECEIVED_SUCCESSFULLY, success=True, data=po_order
    )


@router.patch(
    "/{po_id}/partially-received",
    response_model=StandardResponse[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Partially Receive Purchase Order",
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def purchase_order_partially_received(
    payload: PartiallyReceivePayload,
    po_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: PurchaseOrderService = Depends(get_po_service),
    current_user: dict = Depends(get_current_user),
):
    """Partially receive items for a purchase order and update inventory.

    Executes a PATCH request to `/purchase-orders/{po_id}/partially-received` to receive a subset of items.

    Args:
        payload (PartiallyReceivePayload): The quantities of items received.
        po_id (int): The unique ID of the PO.
        db (AsyncSession): The asynchronous database session dependency.
        service (PurchaseOrderService): The PO service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the quantities are invalid or exceed ordered amounts.
        HTTPException (403): If the user lacks Admin or Manager privileges.
        HTTPException (404): If the PO is not found.

    Returns:
        StandardResponse[PurchaseOrderResponse]: A standardized wrapper with the updated PO.
    """
    org_id = current_user.get("org_id")
    role = current_user.get("role")

    po_order = await service.partially_received_order(db, po_id, payload, role, org_id)
    return StandardResponse(
        message=PurchaseOrderMessages.PARTIALLY_RECEIVED, success=True, data=po_order
    )
