"""
Provide schemas for supplier and vendor management.

This module defines Pydantic models for creating, updating, and returning
supplier details, acting as the source of goods for purchase orders.
"""

from datetime import datetime
from pydantic import Field, EmailStr, BaseModel

from app.constants.common_enum import Status


class SupplierCreate(BaseModel):
    """Represent the payload for creating a new supplier via API.

    Used in request bodies to register a new vendor that provides products.
    Excludes organization context which is inferred from the user.

    Attributes:
        name (str): Company or legal name of the supplier.
        contact_person (str): Primary contact individual at the supplier.
        email (EmailStr): Email address for sending purchase orders and communication.
        phone (str): Phone number for the primary contact.
    """

    name: str = Field(..., min_length=3, max_length=100)
    contact_person: str = Field(..., min_length=3)
    email: EmailStr
    phone: str


class SupplierCreateInternal(SupplierCreate):
    """Represent the payload for internal supplier creation.

    Used by the service layer to attach the correct organization context
    to the newly created supplier.

    Attributes:
        organization_id (int): Identifier of the organization registering the supplier.
    """

    organization_id: int


class SupplierResponse(SupplierCreateInternal):
    """Represent a supplier record returned in API responses.

    Used to serialize complete supplier data, including operational status and timestamps.

    Attributes:
        id (int): Unique identifier of the supplier.
        created_at (datetime): Timestamp when the supplier was added.
        updated_at (datetime): Timestamp of the last modification.
        status (Status): Current operational state of the supplier (e.g., ACTIVE).
    """

    id: int
    created_at: datetime
    updated_at: datetime
    status: Status

    model_config = {"from_attributes": True}


class SupplierUpdate(BaseModel):
    """Represent the payload for updating an existing supplier.

    Used in request bodies for patching supplier records. All fields are optional.

    Attributes:
        name (str | None): New company name, if updating.
        contact_person (str | None): New primary contact, if updating.
        email (EmailStr | None): New contact email, if updating.
        phone (str | None): New contact phone number, if updating.
        status (Status | None): New operational status, if updating.
    """

    name: str | None = Field(default=None, min_length=3, max_length=100)
    contact_person: str | None = Field(default=None, min_length=3)
    email: EmailStr | None = None
    phone: str | None = None
    status: Status | None = None
