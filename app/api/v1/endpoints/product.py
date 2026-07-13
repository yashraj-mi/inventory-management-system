"""Provide API endpoints for the Product domain.

This module defines routes for managing product catalog records, including
creation, listing, updating, and deletion within an organization context.
"""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductCreateInternal,
    ProductUpdate,
    ProductResponse,
)
from app.services.product_service import ProductService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.auth import ALLOW_ORG_ADMIN
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params


from app.dependencies.product import get_product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=StandardResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a Product",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[ProductResponse]:
    """Create a new product for the current user's organization.

    Executes a POST request to `/products` to add a new product to the catalog.

    Args:
        payload (ProductCreate): The product details payload.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductService): The product service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[ProductResponse]: A standardized wrapper containing the newly created product.
    """
    org_id = current_user.get("org_id")
    internal_payload = ProductCreateInternal(
        **payload.model_dump(),
        organization_id=org_id,
    )
    product = await service.create(db, internal_payload)
    product_response = ProductResponse.model_validate(product)

    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Product"),
        data=product_response,
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedData[ProductResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all Products",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def list_products(
    db: AsyncSession = Depends(get_db),
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[ProductResponse]]:
    """Retrieve a paginated list of all products for the current user's organization.

    Executes a GET request to `/products` to fetch the product catalog.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductService): The product service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (400): If pagination parameters are invalid.
        HTTPException (403): If the user lacks organization admin privileges.

    Returns:
        StandardResponse[PaginatedData[ProductResponse]]: A paginated list of products.
    """
    org_id = current_user.get("org_id")
    products, total = await service.get_all_by_org(db, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    data = [ProductResponse.model_validate(p) for p in products]

    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Product"),
        data=paginated,
    )


@router.get(
    "/{product_id}",
    response_model=StandardResponse[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a Product by ID",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_product(
    product_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[ProductResponse]:
    """Retrieve details of a specific product.

    Executes a GET request to `/products/{product_id}` to fetch a product by ID.

    Args:
        product_id (int): The unique ID of the product.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductService): The product service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the product ID is invalid.
        HTTPException (403): If the user lacks access to the product.
        HTTPException (404): If the product is not found.

    Returns:
        StandardResponse[ProductResponse]: A standardized wrapper containing the product details.
    """
    org_id = current_user.get("org_id")
    product = await service.get(db, product_id, org_id)

    product_response = ProductResponse.model_validate(product)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Product"),
        data=product_response,
    )


@router.patch(
    "/{product_id}",
    response_model=StandardResponse[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a Product",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def update_product(
    payload: ProductUpdate,
    product_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[ProductResponse]:
    """Update specific fields of an existing product.

    Executes a PATCH request to `/products/{product_id}` to modify a product.

    Args:
        payload (ProductUpdate): The payload containing updated product fields.
        product_id (int): The unique ID of the product to update.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductService): The product service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks access to update the product.
        HTTPException (404): If the product is not found.

    Returns:
        StandardResponse[ProductResponse]: A standardized wrapper containing the updated product.
    """
    org_id = current_user.get("org_id")
    updated_product = await service.update(db, product_id, payload, org_id)
    product_response = ProductResponse.model_validate(updated_product)

    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Product"),
        data=product_response,
    )


@router.delete(
    "/{product_id}",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a Product",
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def delete_product(
    product_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[None]:
    """Permanently delete a product.

    Executes a DELETE request to `/products/{product_id}` to remove a product.

    Args:
        product_id (int): The unique ID of the product to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (ProductService): The product service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the product ID is invalid or cannot be deleted.
        HTTPException (403): If the user lacks access to delete the product.
        HTTPException (404): If the product is not found.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    org_id = current_user.get("org_id")
    await service.delete(db, product_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Product"),
        data=None,
    )
