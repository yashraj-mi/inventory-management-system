"""Provide API endpoints for the Warehouse domain.

This module defines routes for creating, listing, updating, and deleting
warehouses, scoped to the organization hierarchy.
"""

from app.db.models.user import User
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.schemas.response import StandardResponse
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
    WarehouseCreateInternal,
)
from app.services.warehouse_service import WarehouseService
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.schemas.response import PaginatedData
from app.dependencies.pagination import PaginationParams, get_pagination_params

from app.dependencies.warehouse import get_warehouse_service

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.post(
    "",
    response_model=StandardResponse[WarehouseResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_CREATE))],
)
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Create a new warehouse.

    Executes a POST request to `/warehouses` to register a new storage facility.

    Args:
        warehouse_data (WarehouseCreate): The payload containing warehouse details.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (WarehouseService): The warehouse service layer dependency.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[WarehouseResponse]: A standardized wrapper containing the newly created warehouse.
    """
    org_id = current_user.organization_id
    internal_data = WarehouseCreateInternal(
        **warehouse_data.model_dump(), organization_id=org_id
    )
    result = await service.create_warehouse(db, internal_data)
    warehouse = WarehouseResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Warehouse"),
        data=warehouse,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaginatedData[WarehouseResponse]],
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_READ))],
)
async def get_organization_warehouses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Retrieve all warehouses belonging to the current user's organization.

    Executes a GET request to `/warehouses`.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters.
        service (WarehouseService): The warehouse service layer dependency.

    Raises:
        HTTPException (403): If the user lacks access to the organization.
        HTTPException (404): If the organization does not exist.

    Returns:
        StandardResponse[PaginatedData[WarehouseResponse]]: A paginated list of warehouses.
    """
    org_id = current_user.organization_id
    items, total = await service.get_by_organization(
        organization_id=org_id, db=db, params=params
    )
    total_pages = (total + params.size - 1) // params.size
    data = [WarehouseResponse.model_validate(w) for w in items]
    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Warehouses"),
        data=paginated,
    )


@router.get(
    "/{warehouse_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[WarehouseResponse],
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_READ))],
)
async def get_warehouse_by_id(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Retrieve a warehouse by its ID.

    Executes a GET request to `/warehouses/{warehouse_id}`.

    Args:
        warehouse_id (int): The unique ID of the warehouse.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (WarehouseService): The warehouse service layer dependency.

    Raises:
        HTTPException (403): If the user lacks access to the warehouse's organization.
        HTTPException (404): If the warehouse does not exist.

    Returns:
        StandardResponse[WarehouseResponse]: A standardized wrapper containing the warehouse details.
    """
    org_id = current_user.organization_id
    result = await service.get_warehouse(db, warehouse_id, org_id)
    warehouse = WarehouseResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Warehouse"),
        data=warehouse,
    )


@router.patch(
    "/{warehouse_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[WarehouseResponse],
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_UPDATE))],
)
async def update_warehouse(
    warehouse_id: int,
    update_data: WarehouseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Update an existing warehouse.

    Executes a PATCH request to `/warehouses/{warehouse_id}`.

    Args:
        warehouse_id (int): The unique ID of the warehouse to update.
        update_data (WarehouseUpdate): Payload with fields to update.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (WarehouseService): The warehouse service layer dependency.

    Raises:
        HTTPException (400): If the update payload is invalid.
        HTTPException (403): If the user lacks access to the warehouse's organization.
        HTTPException (404): If the warehouse does not exist.

    Returns:
        StandardResponse[WarehouseResponse]: A standardized wrapper containing the updated warehouse.
    """
    org_id = current_user.organization_id
    result = await service.update_warehouse(db, warehouse_id, update_data, org_id)
    warehouse = WarehouseResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Warehouse"),
        data=warehouse,
    )


@router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[None],
    dependencies=[Depends(require_permission(Permissions.WAREHOUSE_DELETE))],
)
async def delete_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Delete a warehouse by ID.

    Executes a DELETE request to `/warehouses/{warehouse_id}`.

    Args:
        warehouse_id (int): The unique ID of the warehouse to delete.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (WarehouseService): The warehouse service layer dependency.

    Raises:
        HTTPException (400): If the warehouse cannot be deleted.
        HTTPException (403): If the user lacks access to the warehouse's organization.
        HTTPException (404): If the warehouse does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    org_id = current_user.organization_id
    await service.delete_warehouse(db, warehouse_id, org_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Warehouse"),
        data=None,
    )
