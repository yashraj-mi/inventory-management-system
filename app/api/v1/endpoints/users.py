"""
users.py module.

Provides core functionality and components for the users domain.
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
from app.constants.user_enum import UserMessages

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    """
    Dependency provider factory to instantiate the UserService layer.

    Returns:
        UserService: An instance of the user business logic service.
    """
    return UserService()


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
    """
    Creates a new user in the system.

    Args:
        payload (UserCreate): The registration payload containing user details.
        background_tasks (BackgroundTasks): Background tasks for email dispatch.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.
        current_user: get current logged_in user's details.

    Returns:
        StandardResponse[UserResponse]: A standardized response containing the created user.
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
    response_model=StandardResponse[list[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get All Users",
    description="Retrieve all users from the system.",
    response_description="List of wrapped users.",
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
)
async def get_all_users(
    db: AsyncSession = Depends(get_db), service: UserService = Depends(get_user_service)
) -> StandardResponse[list[UserResponse]]:
    """
    Retrieves all users from the system.

    Args:
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.

    Returns:
        StandardResponse[list[UserResponse]]: A list of all users.
    """
    users = await service.get_all_users(db)
    # Convert Sequence elements cleanly into Pydantic representations
    validated_users = [UserResponse.model_validate(u) for u in users]
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="User"),
        data=validated_users,
    )


@router.get(
    "/{organization_id}/users",
    response_model=StandardResponse[list[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get all users of an organization",
    description="Validates target organization credentials and retrieves all user profiles linked to its ecosystem context loop partition.",
)
async def get_organization_users(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse[list[UserResponse]]:
    """
    Endpoint handler to intercept platform requests, manage validation processing contexts,
    and output unified JSON arrays structural packets mapped back onto target validation schemas.
    """
    verify_tenant_access(current_user, organization_id)
    # Operational handoff straight down onto application service bounds
    user_data = await service.get_org_users(db=db, org_id=organization_id)

    # Explicit conversion wrapping Pydantic data schemas cleanly inside your custom global layout
    validated_users = [UserResponse.model_validate(user) for user in user_data]

    return StandardResponse(
        success=True,
        message=UserMessages.ORG_USERS_RETRIEVED.format(
            organization_id=organization_id
        ),
        data=validated_users,
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
    """
    Retrieves a specific user by its unique identifier.

    Args:
        user_id (int): The ID of the user to fetch.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.
        current_user: get current logged_in user's details.

    Returns:
        StandardResponse[UserResponse]: The requested user details.
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
    """
    Updates an existing user's information.

    Args:
        payload (UserUpdate): Payload containing the fields to update.
        user_id (int): The ID of the user to update.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.
        current_user: get current logged_in user's details.

    Returns:
        StandardResponse[UserResponse]: The updated user details.
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
    """
    Deletes a user from the system.

    Args:
        user_id (int): The ID of the user to delete.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.
        current_user: get current logged_in user's details.

    Returns:
        Response: An empty 204 No Content response on success.
    """
    existing_user = await service.get_user(db=db, user_id=user_id)
    verify_tenant_access(current_user, existing_user.organization_id)
    await service.delete_user(db=db, user_id=user_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="User"),
        data=None,
    )
