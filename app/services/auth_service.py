from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    PasswordManager,
    create_access_token,
    create_refresh_token,
    refresh_access_token,
)
from app.schemas.auth import UserLogin, TokenResponse, LoginResponse
from app.repositories.auth_repository import AuthRepository
from app.core.exceptions import AppException


class AuthService:
    """Service layer executing business logic for user authentication."""

    def __init__(self, auth_repo: AuthRepository | None = None) -> None:
        self.auth_repo = auth_repo or AuthRepository()

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
            raise AppException(message="Invalid email or password.", status_code=401)

        # Verify password validity against the stored secure cryptographic hash
        is_password_valid = PasswordManager.verify_password(
            payload.password, existing_user.password_hash
        )
        if not is_password_valid:
            raise AppException(message="Invalid email or password.", status_code=401)

        # Generate authorization and session refresh tokens
        access_token = create_access_token(
            data={"sub": str(existing_user.id), "role": str(existing_user.role.value)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(existing_user.id), "role": str(existing_user.role.value)}
        )

        # Update the user's active connection metadata timestamp
        await self.auth_repo.update_last_login(db=db, user=existing_user)
        await db.commit()

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
