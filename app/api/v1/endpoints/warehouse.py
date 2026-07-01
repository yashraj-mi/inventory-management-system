"""
warehouse.py module.

Provides core functionality and components for the warehouse domain.
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
from app.constants.warehouse_enum import WarehouseMessages

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])
warehouse_service = WarehouseService()


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
):
    """
    Creates a new warehouse.

    Args:
        warehouse_data (WarehouseCreate): The warehouse payload.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[WarehouseResponse]: The created warehouse details.
    """
    org_id = current_user.get("org_id")
    internal_data = WarehouseCreateInternal(
        **warehouse_data.model_dump(), organization_id=org_id
    )
    result = await warehouse_service.create_warehouse(db, internal_data)
    warehouse = WarehouseResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=WarehouseMessages.CREATED_SUCCESSFULLY,
        data=warehouse,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[WarehouseResponse]],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_all_warehouses(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all warehouses.

    Args:
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[list[WarehouseResponse]]: A list of all warehouses.
    """
    items = await warehouse_service.get_all_warehouses(db)
    data = [WarehouseResponse.model_validate(item) for item in items]
    return StandardResponse(
        success=True, message=WarehouseMessages.LIST_RETRIEVED, data=data
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
):
    """
    Retrieves a warehouse by its ID.

    Args:
        warehouse_id (int): The ID of the warehouse.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[WarehouseResponse]: The requested warehouse details.
    """
    result = await warehouse_service.get_warehouse(db, warehouse_id)
    verify_tenant_access(current_user, result.organization_id)
    warehouse = WarehouseResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=WarehouseMessages.DETAILS_RETRIEVED,
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
):
    """
    Updates an existing warehouse.

    Args:
        warehouse_id (int): The ID of the warehouse to update.
        update_data (WarehouseUpdate): Payload with fields to update.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[WarehouseResponse]: The updated warehouse details.
    """
    existing_warehouse = await warehouse_service.get_warehouse(db, warehouse_id)
    verify_tenant_access(current_user, existing_warehouse.organization_id)
    result = await warehouse_service.update_warehouse(db, warehouse_id, update_data)
    warehouse = WarehouseResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=WarehouseMessages.UPDATED_SUCCESSFULLY,
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
):
    """
    Deletes a warehouse by ID.

    Args:
        warehouse_id (int): The ID of the warehouse to delete.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[None]: Success message.
    """
    existing_warehouse = await warehouse_service.get_warehouse(db, warehouse_id)
    verify_tenant_access(current_user, existing_warehouse.organization_id)
    await warehouse_service.delete_warehouse(db, warehouse_id)
    return StandardResponse(
        success=True, message=WarehouseMessages.DELETED_SUCCESSFULLY, data=None
    )


@router.get(
    "/organization/{organization_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[WarehouseResponse]],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_organization_warehouses(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves all warehouses belonging to a specific organization.

    Args:
        organization_id (int): The ID of the organization.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[list[WarehouseResponse]]: A list of warehouses.
    """
    verify_tenant_access(current_user, organization_id)
    warehouses = await warehouse_service.get_by_organization(
        organization_id=organization_id, db=db
    )
    return StandardResponse(
        success=True,
        message=WarehouseMessages.ORG_WAREHOUSES_RETRIEVED,
        data=[WarehouseResponse.model_validate(w) for w in warehouses],
    )
