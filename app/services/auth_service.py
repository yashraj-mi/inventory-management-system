"""
auth_service.py module.

Provides core functionality and components for the auth_service domain.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.core.security import (
    PasswordManager,
    create_access_token,
    create_refresh_token,
    refresh_access_token,
)
from app.schemas.auth import UserLogin, TokenResponse, LoginResponse
from app.repositories.auth_repository import AuthRepository
from app.core.exceptions import AppException
from app.constants.common_enum import Status
from app.constants.organization_enum import OrganizationStatus
from app.repositories.organization_repository import OrganizationRepository
from app.constants.auth_enum import AuthMessages


class AuthService:
    """Service layer executing business logic for user authentication."""

    def __init__(self, auth_repo: AuthRepository | None = None) -> None:
        """
        Executes the __init__ operation.

        Args:
            auth_repo: Parameter description.

        Returns:
            Execution result.
        """
        self.auth_repo = auth_repo or AuthRepository()
        self.org_repo = OrganizationRepository()

    async def login(self, db: AsyncSession, payload: UserLogin) -> LoginResponse:
        """Authenticates a user, updates their login history, and generates secure session tokens.

        Args:
            db (AsyncSession): The active database session state.
            payload (UserLogin): User credentials containing email and password.

        Returns:
            LoginResponse: The authenticated User's generated tokens.

        Raises:
            AppException: For invalid credentials (401).
        """
        existing_user = await self.auth_repo.get_user(db=db, email=payload.email)

        if not existing_user:
            raise AppException(
                message=AuthMessages.INVALID_CREDENTIALS,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Verify password validity against the stored secure cryptographic hash
        is_password_valid = PasswordManager.verify_password(
            payload.password, existing_user.password_hash
        )
        if not is_password_valid:
            raise AppException(
                message=AuthMessages.INVALID_CREDENTIALS,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Check if the user account is active
        if existing_user.status != Status.ACTIVE:
            raise AppException(
                message=AuthMessages.INACTIVE_USER,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Check if the user's organization is active
        org = await self.org_repo.get_by_id(db, existing_user.organization_id)
        if org and org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=AuthMessages.INACTIVE_ORG,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Generate authorization and session refresh tokens
        token_data_payload = {
            "sub": str(existing_user.id),
            "role": str(existing_user.role.value),
            "org_id": existing_user.organization_id,
        }
        access_token = create_access_token(data=token_data_payload)
        refresh_token = create_refresh_token(data=token_data_payload)

        # Update the user's active connection metadata timestamp
        await self.auth_repo.update_last_login(db=db, user=existing_user)

        token_data = LoginResponse(
            access_token=access_token, refresh_token=refresh_token
        )

        return token_data

    async def refresh_token(
        self,
        token: str,
    ) -> TokenResponse:
        """
        Refresh an access token using a valid refresh token.

        Validates the provided refresh token and generates
        a new access token for the authenticated user without
        requiring them to log in again.

        Args:
            token (str):
                Valid refresh token issued during authentication.

        Returns:
            TokenResponse:
                Response object containing the newly generated
                access token.
        """
        return TokenResponse(access_token=refresh_access_token(token))
