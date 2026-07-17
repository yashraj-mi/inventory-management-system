"""Provide API endpoints for the Supplier domain.

This module defines routes for managing supplier records, allowing creation,
listing, updating, and deletion scoped by the user's organization.
"""

from app.db.models.user import User
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.supplier import (
    SupplierCreate,
    SupplierCreateInternal,
    SupplierUpdate,
    SupplierResponse,
)
from app.services.supplier_service import SupplierService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params


from app.dependencies.supplier import get_supplier_service

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post(
    "",
    response_model=StandardResponse[SupplierResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a Supplier",
    dependencies=[Depends(require_permission(Permissions.SUPPLIER_CREATE))],
)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[SupplierResponse]:
    """Create a new supplier for the current user's organization.

    Executes a POST request to `/suppliers` to add a new supplier record.

    Args:
        payload (SupplierCreate): The supplier creation payload.
        db (AsyncSession): The asynchronous database session dependency.
        service (SupplierService): The supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[SupplierResponse]: A standardized wrapper containing the new supplier details.
    """
    org_id = current_user.organization_id
    internal_payload = SupplierCreateInternal(
        **payload.model_dump(), organization_id=org_id
    )
    supplier = await service.create(db, internal_payload)
    supplier_response = SupplierResponse.model_validate(supplier)

    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Supplier"),
        data=supplier_response,
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedData[SupplierResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all Suppliers",
    dependencies=[Depends(require_permission(Permissions.SUPPLIER_READ))],
)
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[SupplierResponse]]:
    """Retrieve a paginated list of all suppliers for the current user's organization.

    Executes a GET request to `/suppliers`.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        service (SupplierService): The supplier service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters.

    Raises:
        HTTPException (400): If pagination parameters are invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[PaginatedData[SupplierResponse]]: A paginated list of suppliers.
    """
    org_id = current_user.organization_id
    suppliers, total = await service.get_all_by_org(db, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    data = [SupplierResponse.model_validate(s) for s in suppliers]

    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Supplier"),
        data=paginated,
    )


@router.get(
    "/{supplier_id}",
    response_model=StandardResponse[SupplierResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a Supplier by ID",
    dependencies=[Depends(require_permission(Permissions.SUPPLIER_READ))],
)
async def get_supplier(
    supplier_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[SupplierResponse]:
    """Retrieve details of a specific supplier.

    Executes a GET request to `/suppliers/{supplier_id}`.

    Args:
        supplier_id (int): The unique ID of the supplier.
        db (AsyncSession): The asynchronous database session dependency.
        service (SupplierService): The supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the supplier ID is invalid.
        HTTPException (403): If the user lacks access to the supplier's organization.
        HTTPException (404): If the supplier is not found.

    Returns:
        StandardResponse[SupplierResponse]: A standardized wrapper containing the supplier details.
    """
    supplier = await service.get(db, supplier_id, current_user.organization_id)

    supplier_response = SupplierResponse.model_validate(supplier)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Supplier"),
        data=supplier_response,
    )


@router.patch(
    "/{supplier_id}",
    response_model=StandardResponse[SupplierResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a Supplier",
    dependencies=[Depends(require_permission(Permissions.SUPPLIER_UPDATE))],
)
async def update_supplier(
    payload: SupplierUpdate,
    supplier_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[SupplierResponse]:
    """Update specific fields of an existing supplier.

    Executes a PATCH request to `/suppliers/{supplier_id}` to modify supplier details.

    Args:
        payload (SupplierUpdate): The payload containing updated fields.
        supplier_id (int): The unique ID of the supplier to update.
        db (AsyncSession): The asynchronous database session dependency.
        service (SupplierService): The supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks access to the supplier's organization.
        HTTPException (404): If the supplier is not found.

    Returns:
        StandardResponse[SupplierResponse]: A standardized wrapper containing the updated supplier.
    """
    updated_supplier = await service.update(
        db, supplier_id, payload, current_user.organization_id
    )
    supplier_response = SupplierResponse.model_validate(updated_supplier)

    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Supplier"),
        data=supplier_response,
    )


@router.delete(
    "/{supplier_id}",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a Supplier",
    dependencies=[Depends(require_permission(Permissions.SUPPLIER_DELETE))],
)
async def delete_supplier(
    supplier_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[None]:
    """Permanently delete a supplier.

    Executes a DELETE request to `/suppliers/{supplier_id}`.

    Args:
        supplier_id (int): The unique ID of the supplier to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (SupplierService): The supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the supplier ID is invalid or deletion is restricted.
        HTTPException (403): If the user lacks access to delete the supplier.
        HTTPException (404): If the supplier is not found.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    await service.delete(db, supplier_id, current_user.organization_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Supplier"),
        data=None,
    )
