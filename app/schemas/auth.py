from pydantic import Field, EmailStr, BaseModel


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=30)


class LoginResponse(BaseModel):
    """Data transfer object for authentication tokens returned to the client."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    token: str
