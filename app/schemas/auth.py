"""
auth.py module.

Provides core functionality and components for the auth domain.
"""

from pydantic import Field, EmailStr, BaseModel


class UserLogin(BaseModel):
    """
    Schema for user login credentials.

    Attributes:
        email (EmailStr): User's email address.
        password (str): User's plain text password.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """
    Data transfer object for authentication tokens returned to the client upon successful login.

    Attributes:
        access_token (str): JWT access token.
        refresh_token (str): JWT refresh token.
        token_type (str): Type of the token, usually "bearer".
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """
    Schema for returning a single token, such as after a refresh operation.

    Attributes:
        access_token (str): The new JWT access token.
        token_type (str): Type of the token, usually "bearer".
    """

    access_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    """
    Schema for validating a token provided in the request body (e.g., for refresh).

    Attributes:
        token (str): The JWT token string.
    """

    token: str = Field(..., min_length=1)
