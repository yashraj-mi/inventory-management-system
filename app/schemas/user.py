"""
user.py module.

Provides core functionality and components for the user domain.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.constants.user_enum import UserRole
from app.constants.common_enum import Status


class UserCreate(BaseModel):
    """
    Schema for creating a new user.
    """

    role: UserRole

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)

    email: EmailStr

    @field_validator("role")
    @classmethod
    def restrict_role(cls, v: UserRole) -> UserRole:
        """Prevent creation of SUPER_ADMIN users via the API."""
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Cannot create a user with SUPER_ADMIN role.")
        return v


class UserCreateInternal(UserCreate):
    """
    Internal schema for user creation.
    Injects organization_id from context and an auto-generated secure password.
    """

    organization_id: int
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
    last_name: str | None

    email: EmailStr

    last_login: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
