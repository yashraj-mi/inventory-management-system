"""
Provide schemas for user management and authentication.

This module contains Pydantic models for onboarding, updating, and returning
user details within an organization's context, including role restrictions.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.constants.user_enum import UserRole
from app.constants.common_enum import Status


class UserCreate(BaseModel):
    """Represent the payload for creating a new user via API.

    Used in request bodies by organization admins to invite or create staff accounts,
    enforcing role limitations (e.g., preventing SUPER_ADMIN creation).

    Attributes:
        role (UserRole): The authorization level assigned to the new user.
        first_name (str): User's given name.
        last_name (str | None): User's family name.
        email (EmailStr): User's email, used for login and notifications.
    """

    role: UserRole

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)

    email: EmailStr

    @field_validator("role")
    @classmethod
    def restrict_role(cls, v: UserRole) -> UserRole:
        """Prevent creation of SUPER_ADMIN users via the standard API payload.

        Args:
            v: The requested UserRole.

        Returns:
            UserRole: The validated role.

        Raises:
            ValueError: If the role is SUPER_ADMIN.
        """
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Cannot create a user with SUPER_ADMIN role.")
        return v


class UserCreateInternal(UserCreate):
    """Represent the payload for internal user creation.

    Used by the service layer to append system-managed context, such as the
    tenant organization and an auto-generated or initial secure password.

    Attributes:
        organization_id (int): Identifier of the organization the user belongs to.
        password (str): The plain-text initial password to be hashed before saving.
    """

    organization_id: int
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Represent the payload for modifying an existing user's details.

    Used in request bodies for PATCH endpoints, allowing partial updates to a profile.

    Attributes:
        role (UserRole | None): New authorization level, if updating.
        first_name (str | None): New given name, if updating.
        last_name (str | None): New family name, if updating.
        email (EmailStr | None): New email address, if updating.
        status (Status | None): New operational status (e.g., suspending the user).
    """

    role: UserRole | None = None

    first_name: str | None = Field(default=None, min_length=2, max_length=100)

    last_name: str | None = Field(default=None, min_length=2, max_length=100)

    email: EmailStr | None = None

    status: Status | None = None


class UserResponse(BaseModel):
    """Represent a user record returned in API responses.

    Used to serialize staff profiles for administrative views, omitting sensitive
    data like password hashes while providing tracking timestamps.

    Attributes:
        id (int): Unique identifier of the user.
        organization_id (int): Identifier of the user's organization.
        role (UserRole): The user's authorization level.
        status (Status): Current operational status (e.g., ACTIVE).
        first_name (str): Given name.
        last_name (str | None): Family name.
        email (EmailStr): Login email address.
        last_login (datetime | None): Timestamp of most recent successful login.
        created_at (datetime): Timestamp of account creation.
        updated_at (datetime): Timestamp of the last profile modification.
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
