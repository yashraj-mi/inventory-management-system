from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.constants.user_enum import UserRole
from app.constants.common_enum import Status


class UserCreate(BaseModel):
    """
    Schema for creating a new user.
    """

    organization_id: int

    role: UserRole

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user's details.
    Fields are optional; only provided fields will be updated.
    """

    role: UserRole | None = None

    first_name: str | None = Field(default=None, min_length=2, max_length=100)

    last_name: str | None = Field(default=None, min_length=2, max_length=100)

    email: EmailStr | None = None

    status: Status | None = None


class UserResponse(BaseModel):
    """
    Schema for returning user details in API responses.
    """

    id: int

    organization_id: int

    role: UserRole
    status: Status

    first_name: str
    last_name: str

    email: EmailStr

    last_login: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
