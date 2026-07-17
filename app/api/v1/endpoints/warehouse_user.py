"""Provide API endpoints for the Warehouse User domain.

This module defines routes for assigning, listing, and removing users from
specific warehouses.
"""

from app.db.models.user import User
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.warehouse_user import WarehouseUserResponse, WarehouseUserAssign
from app.services.warehouse_user_service import WarehouseUserService
from app.schemas.response import StandardResponse
from app.core.security import get_current_user
from app.core.exceptions import AppException
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.services.warehouse_service import WarehouseService
from app.constants.warehouse_user_enum import WarehouseUserMessages
from app.constants.auth_enum import AuthMessages
from app.schemas.response import PaginatedData
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.dependencies.warehouse_user import get_warehouse_user_service
from app.dependencies.warehouse import get_warehouse_service

router = APIRouter(prefix="/warehouses", tags=["Warehouse Users"])


@router.get(
    "/{warehouse_id}/users",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaginatedData[WarehouseUserResponse]],
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_USER_READ))],
    summary="List all users assigned to a warehouse",
)
async def list_warehouse_users(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    service: WarehouseUserService = Depends(get_warehouse_user_service),
    warehouse_svc: WarehouseService = Depends(get_warehouse_service),
    current_user: User = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
):
    """Fetch a collection of all user tracking records explicitly linked to a warehouse.

    Executes a GET request to `/warehouses/{warehouse_id}/users`.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        db (AsyncSession): The asynchronous database session dependency.
        service (WarehouseUserService): The warehouse user service layer dependency.
        warehouse_svc (WarehouseService): The warehouse service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters.

    Raises:
        HTTPException (403): If the user lacks proper access to the organization's warehouse.
        HTTPException (404): If the warehouse does not exist.

    Returns:
        StandardResponse[PaginatedData[WarehouseUserResponse]]: A paginated list of warehouse assignments.
    """
    await warehouse_svc.get_warehouse(db, warehouse_id, current_user.organization_id)
    assignments, total = await service.list_users_in_warehouse(db, warehouse_id, params)
    total_pages = (total + params.size - 1) // params.size
    data = [WarehouseUserResponse.model_validate(a) for a in assignments]
    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=WarehouseUserMessages.LIST_RETRIEVED,
        data=paginated,
    )


@router.post(
    "/{warehouse_id}/users",
    response_model=StandardResponse[WarehouseUserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_USER_ASSIGN))],
    summary="Assign a user to a warehouse",
)
async def assign_user(
    warehouse_id: int,
    payload: WarehouseUserAssign,
    db: AsyncSession = Depends(get_db),
    service: WarehouseUserService = Depends(get_warehouse_user_service),
    warehouse_svc: WarehouseService = Depends(get_warehouse_service),
    current_user: User = Depends(get_current_user),
):
    """Map an isolated staff user ID context directly onto a structural target warehouse location.

    Executes a POST request to `/warehouses/{warehouse_id}/users` to assign a user to a warehouse.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        payload (WarehouseUserAssign): Payload containing the user ID.
        db (AsyncSession): The asynchronous database session dependency.
        service (WarehouseUserService): The warehouse user service layer dependency.
        warehouse_svc (WarehouseService): The warehouse service layer dependency.
        current_user (dict): The authenticated user context performing the action.

    Raises:
        HTTPException (400): If the assignment already exists.
        HTTPException (401): If the current user token is invalid.
        HTTPException (403): If the user lacks admin or manager privileges.
        HTTPException (404): If the warehouse or user does not exist.

    Returns:
        StandardResponse[WarehouseUserResponse]: A standardized wrapper containing the newly created assignment.
    """
    sub = str(current_user.id)
    if not sub:
        raise AppException(
            message=AuthMessages.INVALID_TOKEN, status_code=status.HTTP_401_UNAUTHORIZED
        )
    actor_id = int(sub)

    await warehouse_svc.get_warehouse(db, warehouse_id, current_user.organization_id)

    assignment = await service.assign_user_to_warehouse(
        db, warehouse_id, payload, actor_id
    )
    assignment = WarehouseUserResponse.model_validate(assignment)
    return StandardResponse(
        success=True,
        message=WarehouseUserMessages.ASSIGNED_SUCCESSFULLY,
        data=assignment,
    )


@router.delete(
    "/{warehouse_id}/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[None],
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_USER_REMOVE))],
    summary="Remove a user from a warehouse",
)
async def remove_user(
    warehouse_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: WarehouseUserService = Depends(get_warehouse_user_service),
    warehouse_svc: WarehouseService = Depends(get_warehouse_service),
    current_user: User = Depends(get_current_user),
):
    """Unlink a targeting user row context from mapping paths matching back to the specified warehouse.

    Executes a DELETE request to `/warehouses/{warehouse_id}/users/{user_id}`.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        user_id (int): The unique ID of the user to unassign.
        db (AsyncSession): The asynchronous database session dependency.
        service (WarehouseUserService): The warehouse user service layer dependency.
        warehouse_svc (WarehouseService): The warehouse service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (403): If the user lacks admin or manager privileges.
        HTTPException (404): If the warehouse or assignment does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful removal.
    """
    await warehouse_svc.get_warehouse(db, warehouse_id, current_user.organization_id)
    await service.remove_user_from_warehouse(db, warehouse_id, user_id)
    return StandardResponse(
        success=True,
        message=WarehouseUserMessages.REMOVED_SUCCESSFULLY,
        data=None,
    )
