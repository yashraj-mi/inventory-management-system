from fastapi import APIRouter, Depends, Response, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.schemas.response import StandardResponse
from app.dependencies.auth import (
    ALLOW_ADMIN_OR_MANAGER,
    ALLOW_SUPER_ADMIN,
    ALLOW_SUPER_ADMIN_OR_ORG_ADMIN,
    ALLOW_COMMON_ORG,
)

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
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> StandardResponse[UserResponse]:
    """
    Creates a new user in the system.

    Args:
        payload (UserCreate): The registration payload containing user details.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.

    Returns:
        StandardResponse[UserResponse]: A standardized response containing the created user.
    """
    user_data = await service.create_user(db=db, payload=payload)
    return StandardResponse(
        success=True,
        message="User created successfully.",
        data=UserResponse.model_validate(user_data),
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
        message="List of all users retrieved successfully.",
        data=validated_users,
    )


@router.get(
    "/{organization_id}/users",
    response_model=StandardResponse[list[UserResponse]],
    status_code=200,
    summary="Get all users of an organization",
    description="Validates target organization credentials and retrieves all user profiles linked to its ecosystem context loop partition.",
)
async def get_organization_users(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> StandardResponse[list[UserResponse]]:
    """
    Endpoint handler to intercept platform requests, manage validation processing contexts,
    and output unified JSON arrays structural packets mapped back onto target validation schemas.
    """
    # Operational handoff straight down onto application service bounds
    user_data = await service.get_org_users(db=db, org_id=organization_id)

    # Explicit conversion wrapping Pydantic data schemas cleanly inside your custom global layout
    validated_users = [UserResponse.model_validate(user) for user in user_data]

    return StandardResponse(
        success=True,
        message=f"Successfully retrieved all member accounts provisioned inside organization ID: {organization_id}.",
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
) -> StandardResponse[UserResponse]:
    """
    Retrieves a specific user by its unique identifier.

    Args:
        user_id (int): The ID of the user to fetch.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.

    Returns:
        StandardResponse[UserResponse]: The requested user details.
    """
    user_data = await service.get_user(db=db, user_id=user_id)
    return StandardResponse(
        success=True,
        message="User details retrieved successfully.",
        data=UserResponse.model_validate(user_data),
    )


@router.put(
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
) -> StandardResponse[UserResponse]:
    """
    Updates an existing user's information.

    Args:
        payload (UserUpdate): Payload containing the fields to update.
        user_id (int): The ID of the user to update.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.

    Returns:
        StandardResponse[UserResponse]: The updated user details.
    """
    updated_user = await service.update_user(db=db, user_id=user_id, payload=payload)
    return StandardResponse(
        success=True,
        message="User updated successfully.",
        data=UserResponse.model_validate(updated_user),
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete a user from the system.",
    dependencies=[Depends(ALLOW_ADMIN_OR_MANAGER)],
)
async def delete_user(
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> Response:
    """
    Deletes a user from the system.

    Args:
        user_id (int): The ID of the user to delete.
        db (AsyncSession): The active database session context.
        service (UserService): The user service layer.

    Returns:
        Response: An empty 204 No Content response on success.
    """
    await service.delete_user(db=db, user_id=user_id)
    # Standard: HTTP 204 responses MUST remain completely bodyless
    return Response(status_code=status.HTTP_204_NO_CONTENT)
