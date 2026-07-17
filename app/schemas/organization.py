"""
Provide schemas for organization and tenant management.

This module contains Pydantic models for onboarding, updating, and returning
tenant organization details within the multi-tenant system.
"""

from datetime import datetime
from pydantic import Field, EmailStr, BaseModel, ConfigDict
from app.constants.organization_enum import OrganizationStatus


class OrganizationCreate(BaseModel):
    """Represent the payload for creating a new organization registration request.

    Used in unauthenticated request bodies when a new tenant signs up for the platform.

    Attributes:
        name (str): The organization's legal or trade name (3-200 characters).
        email (EmailStr): Primary contact email for the organization.
        phone (str): Primary contact phone number (3-15 characters).
        address (str): Physical or billing address (20-500 characters).
    """

    name: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=15)
    address: str = Field(..., min_length=20, max_length=500)


class OrganizationStatusUpdate(BaseModel):
    """Represent the payload for updating an organization's operational status.

    Used in request bodies by Super Admins to approve, reject, or deactivate a tenant organization.

    Attributes:
        status (OrganizationStatus): The new operational state to apply to the organization.
    """

    status: OrganizationStatus = Field(
        ..., description="Change status to ACTIVE, INACTIVE, REJECTED, etc."
    )


class OrganizationResponse(BaseModel):
    """Represent an organization record returned in API responses.

    Used to serialize tenant data for administrative interfaces and tenant configuration checks.

    Attributes:
        id (int): Unique identifier of the organization.
        name (str): The organization's legal or trade name.
        email (EmailStr): Primary contact email.
        phone (str): Primary contact phone number.
        address (str): Physical or billing address.
        status (OrganizationStatus): Current operational state of the tenant.
        action_by (int | None): ID of the admin user who last modified the status.
        created_at (datetime): Timestamp when the organization registered.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    name: str
    email: EmailStr
    phone: str
    address: str
    status: OrganizationStatus
    action_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
