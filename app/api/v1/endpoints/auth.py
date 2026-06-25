from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import UserLogin
from app.schemas.response import StandardResponse
from app.services.auth_service import AuthService
from app.schemas.auth import TokenResponse

# Initialize the router with a dedicated prefix and documentation tags
router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service() -> AuthService:
    """Dependency provider factory to instantiate the AuthService layer.

    Returns:
        AuthService: An instance of the authentication business logic service.
    """
    return AuthService()


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
    description="Verify user credentials (email and password) to authenticate them into the system.",
    response_description="Successfully authenticated user profile data.",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> StandardResponse[TokenResponse]:
    """Handles secure user login operations.

    Args:
        payload (UserLogin): The incoming data transfer object containing the
          user's email and password.
        db (AsyncSession): The asynchronous database session dependency.
        service (AuthService): The authentication service layer orchestrator.

    Returns:
        StandardResponse[UserResponse]: A standardized envelope containing the
        authenticated user's profile details.
    """
    # Delegate the credential verification logic to the service layer
    authenticated_user = await service.login(payload=payload, db=db)

    # Wrap the returned user entity inside your global API response structure
    return StandardResponse(
        success=True,
        message="User authenticated successfully.",
        data=authenticated_user,
    )
