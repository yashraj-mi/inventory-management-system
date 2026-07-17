"""Provide API endpoints for the Sales Order domain.

This module defines routes for creating, retrieving, and tracking sales orders,
as well as fulfillment and status transitions.
"""

from app.db.models.user import User
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.sales_order import (
    SalesOrderCreate,
    SalesOrderResponse,
    SalesOrderCreateInternal,
)
from app.constants.sales_order_enum import SalesOrderMessages
from app.services.sales_order_service import SalesOrderService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.dependencies.sales_order import get_sales_order_service
from app.schemas.sales_order import SalesOrderStatusUpdate

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


@router.post(
    "",
    response_model=StandardResponse[SalesOrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a Sales Order",
    dependencies=[Depends(require_permission(Permissions.SALES_ORDER_CREATE))],
)
async def create_sales_order(
    payload: SalesOrderCreate,
    db: AsyncSession = Depends(get_db),
    service: SalesOrderService = Depends(get_sales_order_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[SalesOrderResponse]:
    """Create a new sales order.

    Executes a POST request to `/sales-orders` to generate a sales order.

    Args:
        payload (SalesOrderCreate): The sales order details.
        db (AsyncSession): The asynchronous database session dependency.
        service (SalesOrderService): The sales order service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks proper permissions.

    Returns:
        StandardResponse[SalesOrderResponse]: A standardized wrapper containing the newly created sales order.
    """
    actor_org_id = current_user.organization_id
    actor_id = str(current_user.id)

    internal_payload = SalesOrderCreateInternal(
        **payload.model_dump(), created_by=actor_id, actor_org_id=actor_org_id
    )

    record = await service.create(db, internal_payload)
    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Sales Order"),
        data=record,
    )


@router.get(
    "/warehouse/{warehouse_id}",
    response_model=StandardResponse[PaginatedData[SalesOrderResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get Sales Orders by Warehouse",
    dependencies=[Depends(require_permission(Permissions.SALES_ORDER_READ))],
)
async def get_sales_orders_by_warehouse(
    warehouse_id: int = Path(..., gt=0),
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    service: SalesOrderService = Depends(get_sales_order_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[PaginatedData[SalesOrderResponse]]:
    """Retrieve a paginated list of sales orders for a specific warehouse.

    Executes a GET request to `/sales-orders/warehouse/{warehouse_id}`.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        params (PaginationParams): Pagination parameters.
        db (AsyncSession): The asynchronous database session dependency.
        service (SalesOrderService): The sales order service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If pagination parameters or warehouse ID are invalid.
        HTTPException (403): If the user lacks access to the warehouse.

    Returns:
        StandardResponse[PaginatedData[SalesOrderResponse]]: A paginated list of sales orders.
    """
    actor_org_id = current_user.organization_id
    records, total = await service.get_by_warehouse(
        db, warehouse_id, actor_org_id, params
    )
    total_pages = (total + params.size - 1) // params.size
    return StandardResponse(
        success=True,
        message=CrudMessages.FETCH_SUCCESS.format(module="Sales Orders"),
        data=PaginatedData(
            items=records,
            total=total,
            page=params.page,
            size=params.size,
            pages=total_pages,
        ),
    )


@router.get(
    "/{sales_order_id}",
    response_model=StandardResponse[SalesOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Sales Order",
    dependencies=[Depends(require_permission(Permissions.SALES_ORDER_READ))],
)
async def get_sales_order(
    sales_order_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: SalesOrderService = Depends(get_sales_order_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[SalesOrderResponse]:
    """Retrieve a specific sales order by ID.

    Executes a GET request to `/sales-orders/{sales_order_id}`.

    Args:
        sales_order_id (int): The unique ID of the sales order.
        db (AsyncSession): The asynchronous database session dependency.
        service (SalesOrderService): The sales order service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the sales order ID is invalid.
        HTTPException (403): If the user lacks access to the sales order.
        HTTPException (404): If the sales order is not found.

    Returns:
        StandardResponse[SalesOrderResponse]: A standardized wrapper containing the sales order details.
    """
    actor_org_id = current_user.organization_id
    record = await service.get(db, sales_order_id, actor_org_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Sales Order"),
        data=record,
    )


@router.patch(
    "/{sales_order_id}/status",
    response_model=StandardResponse[SalesOrderResponse],
    dependencies=[Depends(require_permission(Permissions.SALES_ORDER_UPDATE))],
)
async def update_status(
    payload: SalesOrderStatusUpdate,
    sales_order_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
    service: SalesOrderService = Depends(get_sales_order_service),
    current_user: User = Depends(get_current_user),
):
    """Update the lifecycle status of a sales order.

    Executes a PATCH request to `/sales-orders/{sales_order_id}/status` to change order states.

    Args:
        payload (SalesOrderStatusUpdate): The new status to set.
        sales_order_id (int): The unique ID of the sales order.
        db (AsyncSession): The asynchronous database session dependency.
        service (SalesOrderService): The sales order service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the state transition is invalid.
        HTTPException (403): If the user lacks manager or admin privileges.
        HTTPException (404): If the sales order is not found.

    Returns:
        StandardResponse[SalesOrderResponse]: A standardized wrapper containing the updated sales order.
    """

    actor_org_id = current_user.organization_id
    result = await service.update_status(db, sales_order_id, payload, actor_org_id)
    return StandardResponse(
        success=True, message=SalesOrderMessages.STATUS_UPDATED, data=result
    )


from app.schemas.sales_order import PartiallyFulfillPayload


@router.patch(
    "/{sales_order_id}/fulfill",
    response_model=StandardResponse[SalesOrderResponse],
    dependencies=[Depends(require_permission(Permissions.SALES_ORDER_UPDATE))],
)
async def fulfill_sales_order(
    sales_order_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: SalesOrderService = Depends(get_sales_order_service),
    current_user: User = Depends(get_current_user),
):
    """Mark a sales order as fully fulfilled.

    Executes a PATCH request to `/sales-orders/{sales_order_id}/fulfill` to process order completion.

    Args:
        sales_order_id (int): The unique ID of the sales order to fulfill.
        db (AsyncSession): The asynchronous database session dependency.
        service (SalesOrderService): The sales order service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the order is already fulfilled or invalid.
        HTTPException (403): If the user lacks proper managerial access.
        HTTPException (404): If the sales order is not found.

    Returns:
        StandardResponse[SalesOrderResponse]: A standardized wrapper indicating full fulfillment.
    """
    org_id = current_user.organization_id
    so_order = await service.fulfill_order(db, sales_order_id, org_id)
    return StandardResponse(
        message=SalesOrderMessages.FULFILLED_SUCCESSFULLY, success=True, data=so_order
    )


@router.patch(
    "/{sales_order_id}/partially-fulfill",
    response_model=StandardResponse[SalesOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Partially Fulfill Sales Order",
    dependencies=[Depends(require_permission(Permissions.SALES_ORDER_UPDATE))],
)
async def partially_fulfill_sales_order(
    payload: PartiallyFulfillPayload,
    sales_order_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: SalesOrderService = Depends(get_sales_order_service),
    current_user: User = Depends(get_current_user),
):
    """Partially fulfill items in a sales order.

    Executes a PATCH request to `/sales-orders/{sales_order_id}/partially-fulfill`.

    Args:
        payload (PartiallyFulfillPayload): Quantities of items fulfilled.
        sales_order_id (int): The unique ID of the sales order.
        db (AsyncSession): The asynchronous database session dependency.
        service (SalesOrderService): The sales order service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the quantities exceed ordered amounts or are invalid.
        HTTPException (403): If the user lacks proper managerial access.
        HTTPException (404): If the sales order is not found.

    Returns:
        StandardResponse[SalesOrderResponse]: A standardized wrapper with the updated sales order.
    """
    org_id = current_user.organization_id
    so_order = await service.partially_fulfill_order(
        db, sales_order_id, payload, org_id
    )
    return StandardResponse(
        message=SalesOrderMessages.PARTIALLY_FULFILLED, success=True, data=so_order
    )
