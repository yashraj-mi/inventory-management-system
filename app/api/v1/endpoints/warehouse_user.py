from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.warehouse_user import WarehouseUserResponse, WarehouseUserAssign
from app.services.warehouse_user_service import WarehouseUserService
from app.schemas.response import StandardResponse
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.dependencies.auth import ALLOW_ADMIN_OR_MANAGER

router = APIRouter(prefix="/warehouses", tags=["Warehouse Users"])


def get_warehouse_user_service() -> WarehouseUserService:
    """
    Dependency provider factory to instantiate the WarehouseUserService layer.

    Returns:
        WarehouseUserService: An instance of the warehouse user business logic service.
    """
    return WarehouseUserService()


@router.get(
    "/{warehouse_id}/users",
    response_model=StandardResponse[List[WarehouseUserResponse]],
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
    summary="List all users assigned to a warehouse",
)
async def list_warehouse_users(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    service: WarehouseUserService = Depends(get_warehouse_user_service),
):
    """
    Fetches a collection of all user tracking records explicitly linked to a warehouse.

    Args:
        warehouse_id (int): The ID of the warehouse.
        db (AsyncSession): The active database session context.
        service (WarehouseUserService): The warehouse user service layer.

    Returns:
        StandardResponse[List[WarehouseUserResponse]]: A list of warehouse assignments.
    """
    assignments = await service.list_users_in_warehouse(db, warehouse_id)
    return StandardResponse(
        success=True,
        message="Warehouse user listings fetched successfully.",
        data=[WarehouseUserResponse.model_validate(a) for a in assignments],
    )


@router.post(
    "/{warehouse_id}/users",
    response_model=StandardResponse[WarehouseUserResponse],
    status_code=200,
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
    summary="Assign a user to a warehouse",
)
async def assign_user(
    warehouse_id: int,
    payload: WarehouseUserAssign,
    db: AsyncSession = Depends(get_db),
    service: WarehouseUserService = Depends(get_warehouse_user_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Maps an isolated staff user ID context directly onto a structural target warehouse location.

    Args:
        warehouse_id (int): The ID of the warehouse.
        payload (WarehouseUserAssign): Payload containing the user ID.
        db (AsyncSession): The active database session context.
        service (WarehouseUserService): The warehouse user service layer.
        current_user (UserResponse): The current authenticated user performing the action.

    Returns:
        StandardResponse[WarehouseUserResponse]: The newly created assignment.
    """
    actor_id = int(current_user.get("sub"))

    assignment = await service.assign_user_to_warehouse(
        db, warehouse_id, payload, actor_id
    )
    return StandardResponse(
        success=True,
        message="User assigned to warehouse successfully.",
        data=WarehouseUserResponse.model_validate(assignment),
    )


@router.delete(
    "/{warehouse_id}/users/{user_id}",
    response_model=StandardResponse[None],
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
    summary="Remove a user from a warehouse",
)
async def remove_user(
    warehouse_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: WarehouseUserService = Depends(get_warehouse_user_service),
):
    """
    Unlinks a targeting user row context from mapping paths matching back to the specified warehouse.

    Args:
        warehouse_id (int): The ID of the warehouse.
        user_id (int): The ID of the user to unassign.
        db (AsyncSession): The active database session context.
        service (WarehouseUserService): The warehouse user service layer.

    Returns:
        StandardResponse[None]: Success message.
    """
    await service.remove_user_from_warehouse(db, warehouse_id, user_id)
    return StandardResponse(
        success=True,
        message="User successfully unassigned from targeting facility context bounds.",
        data=None,
    )
