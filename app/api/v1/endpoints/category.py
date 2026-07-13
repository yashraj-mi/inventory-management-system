"""Provide endpoints for category management.

This module defines routes for creating, retrieving, updating, and deleting
categories, including organization-specific category filtering.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.schemas.response import StandardResponse, PaginatedData
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryCreateInternal,
)
from app.services.category_service import CategoryService
from app.dependencies.auth import (
    ALLOW_ORG_ADMIN,
    ALLOW_SUPER_ADMIN,
    verify_tenant_access,
)
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.dependencies.category import get_category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=StandardResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    """Create a new category.

    Executes a POST request to `/categories` to create a category under the user's organization.

    Args:
        category_data (CategoryCreate): The category payload containing name and details.
        db (AsyncSession): The asynchronous database session dependency injected by `get_db`.
        current_user (dict): The authenticated user context injected by `get_current_user`.
        service (CategoryService): The category service layer dependency.

    Raises:
        HTTPException (400): If category creation fails or payload is invalid.
        HTTPException (403): If the user is not an organization admin.

    Returns:
        StandardResponse[CategoryResponse]: A standardized wrapper with created category details.
    """
    org_id = current_user.get("org_id")
    internal_data = CategoryCreateInternal(
        **category_data.model_dump(), organization_id=org_id
    )
    result = await service.create_category(db, internal_data)
    category = CategoryResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Category"),
        data=category,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaginatedData[CategoryResponse]],
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
)
async def get_all_categories(
    db: AsyncSession = Depends(get_db),
    params: PaginationParams = Depends(get_pagination_params),
    service: CategoryService = Depends(get_category_service),
):
    """Retrieve all categories.

    Executes a GET request to `/categories` to fetch a paginated list of all categories globally.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        params (PaginationParams): Pagination parameters (page and size).
        service (CategoryService): The category service layer dependency.

    Raises:
        HTTPException (403): If the user is not a super admin.

    Returns:
        StandardResponse[PaginatedData[CategoryResponse]]: A paginated list of all categories.
    """
    items, total = await service.get_all_categories(db, params)
    total_pages = (total + params.size - 1) // params.size
    data = [CategoryResponse.model_validate(item) for item in items]
    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Category"),
        data=paginated,
    )


@router.get(
    "/organization/{organization_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaginatedData[CategoryResponse]],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_organization_categories(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
    service: CategoryService = Depends(get_category_service),
):
    """Retrieve all categories belonging to a specific organization.

    Executes a GET request to `/categories/organization/{organization_id}` to fetch
    categories specific to an organization. Requires tenant access validation.

    Args:
        organization_id (int): The unique ID of the organization.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).
        service (CategoryService): The category service layer dependency.

    Raises:
        HTTPException (400): If invalid pagination parameters are provided.
        HTTPException (403): If the user lacks access to the specified organization.
        HTTPException (404): If the organization is not found.

    Returns:
        StandardResponse[PaginatedData[CategoryResponse]]: A paginated list of categories.
    """
    verify_tenant_access(current_user, organization_id)
    items, total = await service.get_by_organization(
        organization_id=organization_id, db=db, params=params
    )
    total_pages = (total + params.size - 1) // params.size
    data = [CategoryResponse.model_validate(w) for w in items]
    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.ORG_DATA_RETRIEVED.format(module="Categories"),
        data=paginated,
    )


@router.get(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[CategoryResponse],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def get_category_by_id(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    """Retrieve a category by its ID.

    Executes a GET request to `/categories/{category_id}` to fetch specific category details.

    Args:
        category_id (int): The ID of the category to retrieve.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (CategoryService): The category service layer dependency.

    Raises:
        HTTPException (400): If the category ID is invalid.
        HTTPException (403): If the user lacks access to the category's organization.
        HTTPException (404): If the category does not exist.

    Returns:
        StandardResponse[CategoryResponse]: A standardized wrapper with category details.
    """
    result = await service.get_category(db, category_id)
    verify_tenant_access(current_user, result.organization_id)
    category = CategoryResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Category"),
        data=category,
    )


@router.patch(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[CategoryResponse],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def update_category(
    category_id: int,
    update_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    """Update an existing category.

    Executes a PATCH request to `/categories/{category_id}` to modify category attributes.

    Args:
        category_id (int): The ID of the category to update.
        update_data (CategoryUpdate): Payload with fields to update.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (CategoryService): The category service layer dependency.

    Raises:
        HTTPException (400): If the update payload is invalid.
        HTTPException (403): If the user lacks access to the category's organization.
        HTTPException (404): If the category does not exist.

    Returns:
        StandardResponse[CategoryResponse]: A standardized wrapper with the updated category details.
    """
    existing_category = await service.get_category(db, category_id)
    verify_tenant_access(current_user, existing_category.organization_id)
    result = await service.update_category(db, category_id, update_data)
    category = CategoryResponse.model_validate(result)
    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Category"),
        data=category,
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[None],
    dependencies=[Depends(ALLOW_ORG_ADMIN)],
)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    """Delete a category by ID.

    Executes a DELETE request to `/categories/{category_id}` to remove a category.

    Args:
        category_id (int): The ID of the category to delete.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (dict): The authenticated user context.
        service (CategoryService): The category service layer dependency.

    Raises:
        HTTPException (400): If the category cannot be deleted (e.g. linked to products).
        HTTPException (403): If the user lacks access to the category's organization.
        HTTPException (404): If the category does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    existing_category = await service.get_category(db, category_id)
    verify_tenant_access(current_user, existing_category.organization_id)
    await service.delete_category(db, category_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Category"),
        data=None,
    )
