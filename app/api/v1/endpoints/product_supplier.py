"""Provide API endpoints for the ProductSupplier mapping domain.

This module defines routes for managing the relationships between products
and suppliers, allowing for mapping, retrieval, updating, and deletion.
"""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.product_supplier import (
    ProductSupplierCreate,
    ProductSupplierUpdate,
    ProductSupplierResponse,
)
from app.services.product_supplier_service import ProductSupplierService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.auth import ALLOW_ORG_ADMIN
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params


from app.dependencies.product_supplier import (
    get_product_supplier_service as get_ps_service,
)

router = APIRouter(prefix="/product-suppliers", tags=["Product Suppliers"])


@router.post(
    "",
    response_model=StandardResponse[ProductSupplierResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Assign a Supplier to a Product",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def create_mapping(
    payload: ProductSupplierCreate,
    db: AsyncSession = Depends(get_db),
    service: ProductSupplierService = Depends(get_ps_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[ProductSupplierResponse]:
    """Create a new mapping assigning a supplier to a product.

    Executes a POST request to `/product-suppliers` to link a product and a supplier.

    Args:
        payload (ProductSupplierCreate): The mapping details.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductSupplierService): The product supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the mapping already exists or payload is invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[ProductSupplierResponse]: A standardized wrapper containing the new mapping.
    """
    org_id = current_user.get("org_id")
    mapping = await service.create(db, payload, org_id)
    response_data = ProductSupplierResponse.model_validate(mapping)

    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="ProductSupplier"),
        data=response_data,
    )


@router.get(
    "/products/{product_id}",
    response_model=StandardResponse[PaginatedData[ProductSupplierResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Suppliers for a Product",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def list_by_product(
    product_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductSupplierService = Depends(get_ps_service),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[ProductSupplierResponse]]:
    """Retrieve a paginated list of all suppliers assigned to a specific product.

    Executes a GET request to `/product-suppliers/products/{product_id}`.

    Args:
        product_id (int): The unique ID of the product.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductSupplierService): The product supplier service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (400): If the product ID or pagination parameters are invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[PaginatedData[ProductSupplierResponse]]: A paginated list of mappings.
    """
    org_id = current_user.get("org_id")
    mappings, total = await service.get_by_product(db, product_id, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    data = [ProductSupplierResponse.model_validate(m) for m in mappings]

    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="ProductSupplier"),
        data=paginated,
    )


@router.get(
    "/suppliers/{supplier_id}",
    response_model=StandardResponse[PaginatedData[ProductSupplierResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Products for a Supplier",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def list_by_supplier(
    supplier_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductSupplierService = Depends(get_ps_service),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[ProductSupplierResponse]]:
    """Retrieve a paginated list of all products assigned to a specific supplier.

    Executes a GET request to `/product-suppliers/suppliers/{supplier_id}`.

    Args:
        supplier_id (int): The unique ID of the supplier.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductSupplierService): The product supplier service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (400): If the supplier ID or pagination parameters are invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[PaginatedData[ProductSupplierResponse]]: A paginated list of mappings.
    """
    org_id = current_user.get("org_id")
    mappings, total = await service.get_by_supplier(db, supplier_id, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    data = [ProductSupplierResponse.model_validate(m) for m in mappings]

    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="ProductSupplier"),
        data=paginated,
    )


@router.patch(
    "/{mapping_id}",
    response_model=StandardResponse[ProductSupplierResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a Product-Supplier mapping",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def update_mapping(
    payload: ProductSupplierUpdate,
    mapping_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductSupplierService = Depends(get_ps_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[ProductSupplierResponse]:
    """Update specific attributes of a product-supplier mapping.

    Executes a PATCH request to `/product-suppliers/{mapping_id}` to modify mapping details.

    Args:
        payload (ProductSupplierUpdate): The attributes to update (like cost_price).
        mapping_id (int): The unique ID of the mapping.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductSupplierService): The product supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks organization admin privileges.
        HTTPException (404): If the mapping does not exist.

    Returns:
        StandardResponse[ProductSupplierResponse]: A standardized wrapper containing the updated mapping.
    """
    org_id = current_user.get("org_id")
    updated_mapping = await service.update(db, mapping_id, payload, org_id)
    response_data = ProductSupplierResponse.model_validate(updated_mapping)

    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="ProductSupplier"),
        data=response_data,
    )


@router.delete(
    "/{mapping_id}",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a Product-Supplier mapping",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def delete_mapping(
    mapping_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductSupplierService = Depends(get_ps_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[None]:
    """Permanently delete a mapping between a product and supplier.

    Executes a DELETE request to `/product-suppliers/{mapping_id}` to remove a mapping.

    Args:
        mapping_id (int): The unique ID of the mapping to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductSupplierService): The product supplier service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the mapping ID is invalid.
        HTTPException (403): If the user lacks organization admin privileges.
        HTTPException (404): If the mapping does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    org_id = current_user.get("org_id")
    await service.delete(db, mapping_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="ProductSupplier"),
        data=None,
    )
