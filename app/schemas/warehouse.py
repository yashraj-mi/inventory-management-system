"""
warehouse.py module.

Provides core functionality and components for the warehouse domain.
"""

import datetime
from typing import Optional
from pydantic import Field, BaseModel, ConfigDict
from app.constants.warehouse_enum import WarehouseStatus


class WarehouseBase(BaseModel):
    """
    Base schema for Warehouse containing common attributes.
    """

    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=30)
    status: WarehouseStatus = WarehouseStatus.ACTIVE


class WarehouseCreate(WarehouseBase):
    """
    Schema for creating a new warehouse. Inherits from WarehouseBase.
    """

    pass


class WarehouseCreateInternal(WarehouseBase):
    """
    Internal schema for creating a warehouse, injecting the organization_id from context.
    """

    organization_id: int


class WarehouseResponse(WarehouseBase):
    """
    Schema for returning warehouse details in API responses.
    """

    id: int
    organization_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseUpdate(BaseModel):
    """
    Schema for updating an existing warehouse. All fields are optional.
    """

    name: Optional[str] = Field(None, min_length=2)
    code: Optional[str] = None
    address: Optional[str] = Field(None, min_length=30)
    status: Optional[WarehouseStatus] = None
