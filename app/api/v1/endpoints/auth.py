"""Provide authentication endpoints for user login and token management.

This module defines routes for verifying user credentials, generating tokens, and
refreshing access tokens using FastAPI's dependency injection system.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import UserLogin, LoginResponse, TokenResponse, Token
from app.schemas.response import StandardResponse
from app.services.auth_service import AuthService
from app.constants.auth_enum import AuthMessages

from app.dependencies.auth import get_auth_service

# Initialize the router with a dedicated prefix and documentation tags
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=StandardResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
    description="Verify user credentials (email and password) to authenticate them into the system.",
    response_description="Successfully authenticated user profile data.",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> StandardResponse[LoginResponse]:
    """Authenticate a user and return login tokens.

    Executes a POST request to `/auth/login` to verify the provided email and password.
    If valid, returns an access token and user information.

    Args:
        payload (UserLogin): The incoming request payload containing the user's email and password.
        db (AsyncSession): The asynchronous database session dependency injected by `get_db`.
        service (AuthService): The authentication service layer orchestrator injected by `get_auth_service`.

    Raises:
        HTTPException (400): If the credentials are invalid.
        HTTPException (403): If the user account is disabled or locked.
        HTTPException (404): If the user does not exist.

    Returns:
        StandardResponse[LoginResponse]: A standardized envelope containing the authenticated user's access tokens and profile.
    """
    # Delegate the credential verification logic to the service layer
    authenticated_user = await service.login(payload=payload, db=db)

    # Wrap the returned user entity inside your global API response structure
    return StandardResponse(
        success=True,
        message=AuthMessages.LOGIN_SUCCESSFUL,
        data=authenticated_user,
    )


@router.post(
    "/refresh-access-token",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Verify refresh token and generate new access token.",
)
async def refresh_access_token(
    body: Token, service: AuthService = Depends(get_auth_service)
) -> StandardResponse[TokenResponse]:
    """Refresh a user's access token using a valid refresh token.

    Executes a POST request to `/auth/refresh-access-token` to validate the refresh
    token and issue a new access token without requiring a full login.

    Args:
        body (Token): The request payload containing the current refresh token.
        service (AuthService): The authentication service dependency injected by `get_auth_service`.

    Raises:
        HTTPException (400): If the provided refresh token is malformed.
        HTTPException (401): If the refresh token is invalid or expired.

    Returns:
        StandardResponse[TokenResponse]: A standard API response containing the newly generated access token.
    """
    new_access_token = await service.refresh_token(body.token)
    return StandardResponse(
        success=True,
        message=AuthMessages.TOKEN_REFRESHED,
        data=new_access_token,
    )
