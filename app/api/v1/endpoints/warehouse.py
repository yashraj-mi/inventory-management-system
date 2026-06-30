from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.schemas.response import StandardResponse
from app.schemas.warehouse import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from app.services.warehouse_service import WarehouseService
from app.dependencies.auth import ALLOW_ORG_ADMIN, ALLOW_SUPER_ADMIN

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])
warehouse_service = WarehouseService()


@router.post(
    "",
    response_model=StandardResponse[WarehouseResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def create_warehouse(
    warehouse_data: WarehouseCreate, db: AsyncSession = Depends(get_db)
):
    """
    Creates a new warehouse.

    Args:
        warehouse_data (WarehouseCreate): The warehouse payload.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[WarehouseResponse]: The created warehouse details.
    """
    result = await warehouse_service.create_warehouse(db, warehouse_data)
    return StandardResponse(
        success=True,
        message="Warehouse created successfully",
        data=WarehouseResponse.model_validate(result),
    )


@router.get(
    "",
    response_model=StandardResponse[list[WarehouseResponse]],
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
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
        success=True, message="Warehouses retrieved successfully", data=data
    )


@router.get(
    "/{warehouse_id}",
    response_model=StandardResponse[WarehouseResponse],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_warehouse_by_id(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a warehouse by its ID.

    Args:
        warehouse_id (int): The ID of the warehouse.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[WarehouseResponse]: The requested warehouse details.
    """
    result = await warehouse_service.get_warehouse(db, warehouse_id)
    return StandardResponse(
        success=True,
        message="Warehouse retrieved successfully",
        data=WarehouseResponse.model_validate(result),
    )


@router.put(
    "/{warehouse_id}",
    response_model=StandardResponse[WarehouseResponse],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def update_warehouse(
    warehouse_id: int, update_data: WarehouseUpdate, db: AsyncSession = Depends(get_db)
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
    result = await warehouse_service.update_warehouse(db, warehouse_id, update_data)
    return StandardResponse(
        success=True,
        message="Warehouse updated successfully",
        data=WarehouseResponse.model_validate(result),
    )


@router.delete(
    "/{warehouse_id}",
    response_model=StandardResponse[None],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def delete_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a warehouse by ID.

    Args:
        warehouse_id (int): The ID of the warehouse to delete.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[None]: Success message.
    """
    await warehouse_service.delete_warehouse(db, warehouse_id)
    return StandardResponse(
        success=True, message="Warehouse deleted successfully", data=None
    )


@router.get(
    "/organization/{organization_id}",
    response_model=StandardResponse[list[WarehouseResponse]],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_organization_warehouses(
    organization_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all warehouses belonging to a specific organization.

    Args:
        organization_id (int): The ID of the organization.
        db (AsyncSession): The active database session context.

    Returns:
        StandardResponse[list[WarehouseResponse]]: A list of warehouses.
    """
    warehouses = await warehouse_service.get_by_organization(
        organization_id=organization_id, db=db
    )
    return StandardResponse(
        success=True,
        message=f"Warehouses from organization: {organization_id} retrieved successfully",
        data=warehouses,
    )
