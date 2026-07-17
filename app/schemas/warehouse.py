"""
Provide schemas for physical warehouse management.

This module contains Pydantic models for defining, updating, and returning
details of storage facilities where inventory is kept.
"""

import datetime
from pydantic import Field, BaseModel, ConfigDict
from app.constants.warehouse_enum import WarehouseStatus


class WarehouseBase(BaseModel):
    """Define shared attributes for a warehouse entity.

    Used as a foundation for creation and response schemas, ensuring
    consistent field validation for location details.

    Attributes:
        name (str): Display name of the facility.
        code (str): Unique internal alphanumeric code for the warehouse.
        address (str): Physical location address, minimum 30 characters.
        status (WarehouseStatus): Current operational status, defaults to ACTIVE.
    """

    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=30)
    status: WarehouseStatus = WarehouseStatus.ACTIVE


class WarehouseCreate(WarehouseBase):
    """Represent the payload for creating a new warehouse via API.

    Used in request bodies by admins to register a new storage location
    without specifying internal context explicitly.
    """

    pass


class WarehouseCreateInternal(WarehouseBase):
    """Represent the payload for internal creation of a warehouse.

    Used by the service layer to append the organization context of the
    tenant registering the facility.

    Attributes:
        organization_id (int): Identifier of the organization that owns this warehouse.
    """

    organization_id: int


class WarehouseResponse(WarehouseBase):
    """Represent a warehouse record returned in API responses.

    Used to serialize facility details alongside system identifiers and timestamps.

    Attributes:
        id (int): Unique identifier of the warehouse.
        organization_id (int): Identifier of the owning organization.
        created_at (datetime.datetime): Timestamp of creation.
        updated_at (datetime.datetime): Timestamp of the last modification.
    """

    id: int
    organization_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseUpdate(BaseModel):
    """Represent the payload for modifying an existing warehouse.

    Used in request bodies for PATCH endpoints. All fields are optional.

    Attributes:
        name (str | None): New name of the facility.
        code (str | None): New unique alphanumeric code.
        address (str | None): New physical location address.
        status (WarehouseStatus | None): New operational status.
    """

    name: str | None = Field(None, min_length=2)
    code: str | None = None
    address: str | None = Field(None, min_length=30)
    status: WarehouseStatus | None = None
