"""Provide API endpoints for the Warehouse domain.

This module defines routes for creating, listing, updating, and deleting
warehouses, scoped to the organization hierarchy.
"""

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
from app.dependencies.auth import ALLOW_ORG_ADMIN, verify_tenant_access
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
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
    org_id = current_user.get("org_id")
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
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_all_warehouses(
    db: AsyncSession = Depends(get_db),
    params: PaginationParams = Depends(get_pagination_params),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Retrieve all warehouses.

    Executes a GET request to `/warehouses` to fetch a paginated list of all warehouses globally.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        params (PaginationParams): Pagination parameters.
        service (WarehouseService): The warehouse service layer dependency.

    Raises:
        HTTPException (403): If the user lacks proper admin privileges.

    Returns:
        StandardResponse[PaginatedData[WarehouseResponse]]: A paginated list of all warehouses.
    """
    items, total = await service.get_all_warehouses(db, params)
    total_pages = (total + params.size - 1) // params.size
    data = [WarehouseResponse.model_validate(item) for item in items]
    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Warehouse"),
        data=paginated,
    )


@router.get(
    "/organization/{organization_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaginatedData[WarehouseResponse]],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_organization_warehouses(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
    service: WarehouseService = Depends(get_warehouse_service),
):
    """Retrieve all warehouses belonging to a specific organization.

    Executes a GET request to `/warehouses/organization/{organization_id}`.

    Args:
        organization_id (int): The unique ID of the organization.
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
    verify_tenant_access(current_user, organization_id)
    items, total = await service.get_by_organization(
        organization_id=organization_id, db=db, params=params
    )
    total_pages = (total + params.size - 1) // params.size
    data = [WarehouseResponse.model_validate(w) for w in items]
    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.ORG_DATA_RETRIEVED.format(module="Warehouses"),
        data=paginated,
    )


@router.get(
    "/{warehouse_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[WarehouseResponse],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_warehouse_by_id(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
    result = await service.get_warehouse(db, warehouse_id)
    verify_tenant_access(current_user, result.organization_id)
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
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def update_warehouse(
    warehouse_id: int,
    update_data: WarehouseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
    existing_warehouse = await service.get_warehouse(db, warehouse_id)
    verify_tenant_access(current_user, existing_warehouse.organization_id)
    result = await service.update_warehouse(db, warehouse_id, update_data)
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
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def delete_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
    existing_warehouse = await service.get_warehouse(db, warehouse_id)
    verify_tenant_access(current_user, existing_warehouse.organization_id)
    await service.delete_warehouse(db, warehouse_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Warehouse"),
        data=None,
    )
