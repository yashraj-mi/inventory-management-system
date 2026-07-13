"""
Authentication service for managing user login and token generation.

This service is responsible for validating user credentials, ensuring the
associated user and organization are active, managing session tokens
(access and refresh), and updating login history metadata.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
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


from app.core.profiling import log_timing


class AuthService:
    """Service layer executing business logic for user authentication."""

    def __init__(
        self, auth_repo: AuthRepository, org_repo: OrganizationRepository
    ) -> None:
        """
        Initialize the AuthService with required repositories.

        Args:
            auth_repo: Repository for user authentication and state retrieval.
            org_repo: Repository for organization validation to ensure business continuity.
        """
        self.auth_repo = auth_repo
        self.org_repo = org_repo

    @log_timing
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
        try:
            await self.auth_repo.update_last_login(db=db, user=existing_user)
            await db.flush()
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=AuthMessages.DB_UNEXPECTED_UPDATE,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        token_data = LoginResponse(
            access_token=access_token, refresh_token=refresh_token
        )

        return token_data

    @log_timing
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
