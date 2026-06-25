from fastapi import APIRouter, Depends, Response, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    return UserService()


@router.post(
    "",
    response_model=StandardResponse[
        UserResponse
    ],  # FIXED: Matches the wrapper structure
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user in the system.",
    response_description="Created user envelope.",
)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> StandardResponse[UserResponse]:
    user_data = await service.create_user(db=db, payload=payload)
    return StandardResponse(
        success=True,
        message="User created successfully.",
        data=UserResponse.model_validate(user_data),
    )


@router.get(
    "",
    response_model=StandardResponse[
        list[UserResponse]
    ],  # FIXED: Inner type wrapped in list
    status_code=status.HTTP_200_OK,
    summary="Get All Users",
    description="Retrieve all users from the system.",
    response_description="List of wrapped users.",
)
async def get_all_users(
    db: AsyncSession = Depends(get_db), service: UserService = Depends(get_user_service)
) -> StandardResponse[list[UserResponse]]:
    users = await service.get_all_users(db)
    # Convert Sequence elements cleanly into Pydantic representations
    validated_users = [UserResponse.model_validate(u) for u in users]
    return StandardResponse(
        success=True,
        message="List of all users retrieved successfully.",
        data=validated_users,
    )


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],  # FIXED: Updated response_model
    status_code=status.HTTP_200_OK,
    summary="Get User By ID",
    description="Retrieve a specific user using its unique identifier.",
    response_description="User profile envelope.",
)
async def get_user(
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> StandardResponse[UserResponse]:
    user_data = await service.get_user(db=db, user_id=user_id)
    return StandardResponse(
        success=True,
        message="User details retrieved successfully.",
        data=UserResponse.model_validate(user_data),
    )


@router.put(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],  # FIXED: Updated response_model
    status_code=status.HTTP_200_OK,
    summary="Update User",
    description="Update an existing user's information.",
    response_description="Updated user profile envelope.",
)
async def update_user(
    payload: UserUpdate,
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> StandardResponse[UserResponse]:
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
)
async def delete_user(
    user_id: int = Path(..., gt=0, description="Unique user identifier."),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> Response:
    await service.delete_user(db=db, user_id=user_id)
    # Standard: HTTP 204 responses MUST remain completely bodyless
    return Response(status_code=status.HTTP_204_NO_CONTENT)
