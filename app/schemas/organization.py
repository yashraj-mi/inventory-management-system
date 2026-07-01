"""
organization.py module.

Provides core functionality and components for the organization domain.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr, BaseModel, ConfigDict
from app.constants.organization_enum import OrganizationStatus


class OrganizationCreate(BaseModel):
    """
    Schema for creating a new organization registration request.

    Attributes:
        name (str): The organization's name (3-200 characters).
        email (EmailStr): Contact email for the organization.
        phone (str): Contact phone number (3-15 characters).
        address (str): Physical address (20-500 characters).
    """

    name: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=15)
    address: str = Field(..., min_length=20, max_length=500)


class OrganizationStatusUpdate(BaseModel):
    """
    Schema for updating an organization's status (typically by a Super Admin).

    Attributes:
        status (OrganizationStatus): The new status to apply.
    """

    status: OrganizationStatus = Field(
        ..., description="Change status to ACTIVE, INACTIVE, REJECTED, etc."
    )


class OrganizationResponse(BaseModel):
    """
    Schema for returning organization details in API responses.

    Attributes:
        id (int): Unique identifier.
        name (str): Organization's name.
        email (EmailStr): Organization's email.
        phone (str): Contact phone.
        address (str): Physical address.
        status (OrganizationStatus): Current status.
        action_by (int, optional): ID of the user who last changed the status.
        created_at (datetime): Timestamp of creation.
        updated_at (datetime): Timestamp of last update.
    """

    id: int
    name: str
    email: EmailStr
    phone: str
    address: str
    status: OrganizationStatus
    action_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
