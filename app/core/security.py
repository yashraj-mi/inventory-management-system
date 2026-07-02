"""
security.py module.

Provides core functionality and components for the security domain.
"""

from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
from jose import jwt, JWTError

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.constants.auth_enum import AuthMessages

settings = get_settings()

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class PasswordManager:
    """
    Utility class for password hashing and verification.

    Uses the recommended hashing algorithm provided by pwdlib
    to securely store and validate user passwords.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Generate a secure hash for a plain-text password.

        Args:
            password (str):
                User's plain-text password.

        Returns:
            str:
                Securely hashed password suitable for database storage.
        """
        return password_hash.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a stored hash.

        Args:
            plain_password (str):
                Password provided by the user.

            hashed_password (str):
                Previously stored password hash.

        Returns:
            bool:
                True if the password matches the hash,
                otherwise False.
        """
        return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generate a JWT access token.

    The token contains the provided payload along with
    expiration information and a token type identifier.

    Args:
        data (dict):
            Payload to include in the JWT.
            Typically contains the user identifier (sub).

        expires_delta (timedelta | None):
            Custom expiration duration. If not provided,
            the default access token lifetime from settings
            will be used.

    Returns:
        str:
            Encoded JWT access token.
    """

    payload = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload.update({"exp": expire, "type": "access"})

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generate a JWT refresh token.

    Refresh tokens are used to obtain new access tokens
    without requiring the user to authenticate again.

    Args:
        data (dict):
            Payload to include in the JWT.
            Typically contains the user identifier (sub).

        expires_delta (timedelta | None):
            Custom expiration duration. If not provided,
            the default refresh token lifetime from settings
            will be used.

    Returns:
        str:
            Encoded JWT refresh token.
    """

    payload = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    payload.update({"exp": expire, "type": "refresh"})

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Verifies the token signature and expiration.

    Args:
        token (str):
            JWT token to decode.

    Returns:
        dict:
            Decoded JWT payload.

    Raises:
        AppException:
            Raised when the token is invalid, expired,
            malformed, or cannot be decoded.
    """

    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

    except JWTError:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED, message=AuthMessages.INVALID_TOKEN
        )


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieve the currently authenticated user payload.

    This dependency extracts the bearer token from the
    Authorization header, validates it, and returns
    the decoded JWT payload.

    Args:
        token (str):
            Access token extracted from the request.

    Returns:
        dict:
            Decoded JWT payload containing user information.

    Raises:
        AppException:
            Raised when the token is invalid or the
            required user identifier is missing.
    """
    payload = decode_token(token)

    user_id = payload.get("sub")
    token_type = payload.get("type")

    if not user_id:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED, message=AuthMessages.INVALID_TOKEN
        )

    if token_type != "access":
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED, message=AuthMessages.INVALID_TOKEN
        )

    return payload


def refresh_access_token(token: str):
    """
    Generate a new access token from a valid refresh token.

    The provided token must be a refresh token and contain
    a valid user identifier.

    Args:
        token (str):
            Refresh token issued during authentication.

    Returns:
        str:
            Newly generated access token.

    Raises:
        AppException:
            Raised when the token is invalid, expired,
            malformed, or not a refresh token.
    """
    payload = decode_token(token)

    user_id = payload.get("sub")
    token_type = payload.get("type")
    role = payload.get("role")
    org_id = payload.get("org_id")

    if not user_id or token_type != "refresh":
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED, message=AuthMessages.INVALID_TOKEN
        )

    new_access_token = create_access_token(
        data={"sub": str(user_id), "role": role, "org_id": org_id}
    )
    return new_access_token
