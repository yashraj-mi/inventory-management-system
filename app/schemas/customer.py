"""
Provide schemas for customer data validation and representation.

This module defines Pydantic models for creating, updating, and returning
customer records within the context of an organization.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    """Represent the payload for creating a new customer via external API.

    Used in request bodies for customer creation endpoints. Excludes system-managed
    fields like organization_id.

    Attributes:
        name (str): Full name of the customer.
        email (str | None): Optional email address for communication.
        phone (str | None): Optional contact phone number.
        address (str | None): Optional physical address for billing or shipping.
    """

    name: str = Field(..., max_length=150)
    email: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None


class CustomerCreateInternal(CustomerCreate):
    """Represent the payload for internal customer creation.

    Used in service-layer logic where the organization context must be explicitly
    provided to associate the customer with the correct tenant.

    Attributes:
        organization_id (int): The unique identifier of the owning organization.
    """

    organization_id: int


class CustomerUpdate(BaseModel):
    """Represent the payload for modifying an existing customer record.

    Used in request bodies for customer update (PATCH) endpoints. All fields are
    optional to support partial updates.

    Attributes:
        name (str | None): The new name of the customer, if updating.
        email (str | None): The new email of the customer, if updating.
        phone (str | None): The new phone number of the customer, if updating.
        address (str | None): The new address of the customer, if updating.
    """

    name: str | None = Field(default=None, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None


class CustomerResponse(BaseModel):
    """Represent a customer record returned in API responses.

    Used to serialize customer data from the database to clients.

    Attributes:
        id (int): Unique identifier of the customer.
        organization_id (int): The organization this customer belongs to.
        name (str): Full name of the customer.
        email (str | None): Email address for communication.
        phone (str | None): Contact phone number.
        address (str | None): Physical address for billing or shipping.
        created_at (datetime): Timestamp when the customer was created.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    organization_id: int
    name: str
    email: str | None
    phone: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
