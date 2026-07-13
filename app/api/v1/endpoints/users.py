"""Provide API endpoints for the User domain.

This module defines routes for user creation, retrieval, updating, and deletion,
along with context-based organization scoping.
"""

from fastapi import APIRouter, Depends, Path, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from app.core.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserCreateInternal
from app.services.user_service import UserService
from app.services.email_service import email_service
from app.schemas.response import StandardResponse
from app.dependencies.auth import (
    ALLOW_ADMIN_OR_MANAGER,
    ALLOW_SUPER_ADMIN,
    ALLOW_SUPER_ADMIN_OR_ORG_ADMIN,
    ALLOW_COMMON_ORG,
    verify_tenant_access,
)
from app.constants.common_enum import CrudMessages
from app.core.security import get_current_user
from app.schemas.response import PaginatedData
from app.dependencies.pagination import PaginationParams, get_pagination_params

from app.dependencies.user import get_user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user in the system.",
    response_description="Created user envelope.",
    dependencies=[Depends(ALLOW_SUPER_ADMIN_OR_ORG_ADMIN)],
)
async def create_user(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[UserResponse]:
    """Create a new user in the system.

    Executes a POST request to `/users` to register a new user under the current organization.

    Args:
        payload (UserCreate): The registration payload containing user details.
        background_tasks (BackgroundTasks): Background tasks for email dispatch.
        db (AsyncSession): The asynchronous database session dependency.
        service (UserService): The user service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the email is already in use.
        HTTPException (403): If the user lacks admin privileges.

    Returns:
        StandardResponse[UserResponse]: A standardized wrapper containing the created user.
    """
    org_id = current_user.get("org_id")
    temp_password = secrets.token_urlsafe(16)
    internal_payload = UserCreateInternal(
        **payload.model_dump(), organization_id=org_id, password=temp_password
    )

    user_data = await service.create_user(db=db, payload=internal_payload)

    email_service.send_credentials_email(
        background_tasks=background_tasks,
        first_name=internal_payload.first_name,
        recipient=internal_payload.email,
        org_name="Your Organization",
        temp_password=temp_password,
    )
    user_data = UserResponse.model_validate(user_data)
    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="User"),
        data=user_data,
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedData[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get All Users",
    description="Retrieve all users from the system.",
    response_description="List of wrapped users.",
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
)
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    params: PaginationParams = Depends(get_pagination_params),
):
    """Retrieve a paginated list of all users from the system.

    Executes a GET request to `/users` to fetch globally registered users.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        service (UserService): The user service layer dependency.
        params (PaginationParams): Pagination parameters.

    Raises:
        HTTPException (403): If the user lacks super admin privileges.

    Returns:
        StandardResponse[PaginatedData[UserResponse]]: A paginated list of all users.
    """
    users, total = await service.get_all_users(db, params)
    total_pages = (total + params.size - 1) // params.size
    # Convert Sequence elements cleanly into Pydantic representations
    validated_users = [UserResponse.model_validate(u) for u in users]
    data = PaginatedData(
        items=validated_users,
        total=total,
        page=params.page,
        size=params.size,
        pages=total_pages,
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="User"),
        data=data,
    )


@router.get(
    "/{organization_id}/users",
    response_model=StandardResponse[PaginatedData[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get all users of an organization",
    description="Validates target organization credentials and retrieves all user profiles linked to its ecosystem context loop partition.",
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def get_organization_users(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
    params: PaginationParams = Depends(get_pagination_params),
):
    """Retrieve a paginated list of all users linked to an organization.

    Executes a GET request to `/{organization_id}/users` to fetch organization staff.

    Args:
        organization_id (int): The unique ID of the organization.
        db (AsyncSession): The asynchronous database session dependency.
        service (UserService): The user service layer dependency.
        current_user (dict): The authenticated user context.
        params (PaginationParams): Pagination parameters.

    Raises:
        HTTPException (400): If the pagination parameters are invalid.
        HTTPException (403): If the user lacks access to the organization.
        HTTPException (404): If the organization does not exist.

    Returns:
        StandardResponse[PaginatedData[UserResponse]]: A paginated list of users.
    """
    verify_tenant_access(current_user, organization_id)
    # Operational handoff straight down onto application service bounds
    user_data, total = await service.get_org_users(
        db=db, org_id=organization_id, params=params
    )
    total_pages = (total + params.size - 1) // params.size

    # Explicit conversion wrapping Pydantic data schemas cleanly inside your custom global layout
    validated_users = [UserResponse.model_validate(user) for user in user_data]
    data = PaginatedData(
        items=validated_users,
        total=total,
        page=params.page,
        size=params.size,
        pages=total_pages,
    )

    return StandardResponse(
        success=True,
        message=CrudMessages.ORG_DATA_RETRIEVED.format(module="Users"),
        data=data,
    )


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User By ID",
    description="Retrieve a specific user using its unique identifier.",
    response_description="User profile envelope.",
    dependencies=[Depends(ALLOW_COMMON_ORG)],
)
async def get_user(
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[UserResponse]:
    """Retrieve a specific user by its unique identifier.

    Executes a GET request to `/users/{user_id}` to fetch a user profile.

    Args:
        user_id (int): The unique ID of the user.
        db (AsyncSession): The asynchronous database session dependency.
        service (UserService): The user service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the user ID is invalid.
        HTTPException (403): If the user lacks access to the requested user profile.
        HTTPException (404): If the user does not exist.

    Returns:
        StandardResponse[UserResponse]: A standardized wrapper containing the user details.
    """
    user_data = await service.get_user(db=db, user_id=user_id)
    verify_tenant_access(current_user, user_data.organization_id)
    user_data = UserResponse.model_validate(user_data)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="User"),
        data=user_data,
    )


@router.patch(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update User",
    description="Update an existing user's information.",
    response_description="Updated user profile envelope.",
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def update_user(
    payload: UserUpdate,
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[UserResponse]:
    """Update an existing user's information.

    Executes a PATCH request to `/users/{user_id}` to modify a user profile.

    Args:
        payload (UserUpdate): Payload containing the fields to update.
        user_id (int): The unique ID of the user to update.
        db (AsyncSession): The asynchronous database session dependency.
        service (UserService): The user service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the payload is invalid.
        HTTPException (403): If the user lacks access to the requested user profile.
        HTTPException (404): If the user does not exist.

    Returns:
        StandardResponse[UserResponse]: A standardized wrapper containing the updated user details.
    """
    existing_user = await service.get_user(db=db, user_id=user_id)
    verify_tenant_access(current_user, existing_user.organization_id)
    updated_user = await service.update_user(db=db, user_id=user_id, payload=payload)
    updated_user = UserResponse.model_validate(updated_user)
    return StandardResponse(
        success=True,
        message=CrudMessages.UPDATE_SUCCESS.format(module="User"),
        data=updated_user,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete User",
    description="Delete a user from the system.",
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def delete_user(
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[None]:
    """Delete a user from the system.

    Executes a DELETE request to `/users/{user_id}`.

    Args:
        user_id (int): The unique ID of the user to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (UserService): The user service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (400): If the user cannot be deleted.
        HTTPException (403): If the user lacks access to delete the user.
        HTTPException (404): If the user does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    existing_user = await service.get_user(db=db, user_id=user_id)
    verify_tenant_access(current_user, existing_user.organization_id)
    await service.delete_user(db=db, user_id=user_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="User"),
        data=None,
    )
