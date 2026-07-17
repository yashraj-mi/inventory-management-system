"""
Provide schemas for authentication and authorization operations.

This module contains Pydantic models used to validate incoming login credentials
and format outgoing authentication token responses.
"""

from pydantic import Field, EmailStr, BaseModel


class UserLogin(BaseModel):
    """Represent user login credentials for authentication requests.

    Used in the request body of login endpoints to authenticate a user.

    Attributes:
        email (EmailStr): User's email address used as the primary identifier.
        password (str): User's plain text password, requiring a minimum of 8 characters.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """Represent the authentication tokens returned upon successful login.

    Used in the response body of login endpoints to provide access and refresh tokens.

    Attributes:
        access_token (str): JWT access token used for authorizing subsequent requests.
        refresh_token (str): JWT refresh token used to obtain new access tokens.
        token_type (str): Type of the token, expected to be 'bearer' for HTTP Bearer authentication.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Represent a single token returned from refresh operations.

    Used in the response body when exchanging a refresh token for a new access token.

    Attributes:
        access_token (str): The newly issued JWT access token.
        token_type (str): Type of the token, expected to be 'bearer' for HTTP Bearer authentication.
    """

    access_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    """Represent a token provided in a request body.

    Used in requests that require a token payload, such as token refresh or revocation.

    Attributes:
        token (str): The raw JWT token string to be processed.
    """

    token: str = Field(..., min_length=1)
