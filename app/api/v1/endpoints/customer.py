"""Provide API endpoints for the Customer domain.

This module defines routes for managing customer records, including creation,
retrieval, updating, and deletion, restricted by user organizations.
"""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.customer import (
    CustomerCreate,
    CustomerCreateInternal,
    CustomerUpdate,
    CustomerResponse,
)
from app.services.customer_service import CustomerService
from app.schemas.response import StandardResponse, PaginatedData
from app.dependencies.auth import ALLOW_COMMON_ORG
from app.core.security import get_current_user
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params


from app.dependencies.customer import get_customer_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=StandardResponse[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Customer Record",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[CustomerResponse]:
    """Create a new customer for the current user's organization.

    Executes a POST request to `/customers` to add a new customer record.

    Args:
        payload (CustomerCreate): The customer creation payload.
        db (AsyncSession): The asynchronous database session dependency.
        service (CustomerService): The customer service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks organization permissions.

    Returns:
        StandardResponse[CustomerResponse]: A standardized wrapper containing the new customer.
    """
    org_id = current_user.get("org_id")
    internal_payload = CustomerCreateInternal(
        **payload.model_dump(), organization_id=org_id
    )

    record = await service.create(db, internal_payload)
    response_data = CustomerResponse.model_validate(record)

    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Customer"),
        data=response_data,
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedData[CustomerResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Customers",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def list_customers(
    db: AsyncSession = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
) -> StandardResponse[PaginatedData[CustomerResponse]]:
    """Retrieve a paginated list of all customers in the current user's organization.

    Executes a GET request to `/customers` to fetch customers linked to the user's tenant.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        service (CustomerService): The customer service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (400): If invalid pagination parameters are provided.
        HTTPException (403): If the user lacks organization permissions.

    Returns:
        StandardResponse[PaginatedData[CustomerResponse]]: A paginated list of customers.
    """
    org_id = current_user.get("org_id")
    records, total = await service.get_all_by_org(db, org_id, params)

    total_pages = (total + params.size - 1) // params.size
    data = [CustomerResponse.model_validate(r) for r in records]

    paginated = PaginatedData(
        items=data, total=total, page=params.page, size=params.size, pages=total_pages
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Customer"),
        data=paginated,
    )


@router.get(
    "/{customer_id}",
    response_model=StandardResponse[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a Customer Record",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def get_customer(
    customer_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[CustomerResponse]:
    """Retrieve a specific customer record by ID.

    Executes a GET request to `/customers/{customer_id}` to fetch a customer.

    Args:
        customer_id (int): The unique ID of the customer.
        db (AsyncSession): The asynchronous database session dependency.
        service (CustomerService): The customer service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the customer ID is invalid.
        HTTPException (403): If the user lacks access to this organization's customer.
        HTTPException (404): If the customer does not exist.

    Returns:
        StandardResponse[CustomerResponse]: A standardized wrapper containing customer details.
    """
    org_id = current_user.get("org_id")
    record = await service.get(db, customer_id, org_id)
    response_data = CustomerResponse.model_validate(record)

    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Customer"),
        data=response_data,
    )


@router.patch(
    "/{customer_id}",
    response_model=StandardResponse[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a Customer Record",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def update_customer(
    payload: CustomerUpdate,
    customer_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[CustomerResponse]:
    """Update specific attributes of a customer.

    Executes a PATCH request to `/customers/{customer_id}` to update customer details.

    Args:
        payload (CustomerUpdate): The payload containing attributes to update.
        customer_id (int): The unique ID of the customer.
        db (AsyncSession): The asynchronous database session dependency.
        service (CustomerService): The customer service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the update payload is invalid.
        HTTPException (403): If the user lacks access to modify this customer.
        HTTPException (404): If the customer does not exist.

    Returns:
        StandardResponse[CustomerResponse]: A standardized wrapper with the updated customer details.
    """
    org_id = current_user.get("org_id")
    updated_record = await service.update(db, customer_id, payload, org_id)
    response_data = CustomerResponse.model_validate(updated_record)

    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="Customer"),
        data=response_data,
    )


@router.delete(
    "/{customer_id}",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a Customer Record",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def delete_customer(
    customer_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[None]:
    """Permanently delete a customer record.

    Executes a DELETE request to `/customers/{customer_id}` to remove a customer.

    Args:
        customer_id (int): The unique ID of the customer to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (CustomerService): The customer service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the customer cannot be deleted (e.g. linked to sales orders).
        HTTPException (403): If the user lacks access to delete this customer.
        HTTPException (404): If the customer does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    org_id = current_user.get("org_id")
    await service.delete(db, customer_id, org_id)

    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Customer"),
        data=None,
    )
