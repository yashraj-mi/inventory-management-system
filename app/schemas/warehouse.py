import datetime
from typing import Optional
from pydantic import Field, BaseModel
from app.constants.warehouse_enum import WarehouseStatus


class WarehouseBase(BaseModel):
    """
    Base schema for Warehouse containing common attributes.
    """

    organization_id: int
    name: str = Field(..., min_length=2)
    code: str
    address: str = Field(..., min_length=30)
    status: WarehouseStatus


class WarehouseCreate(WarehouseBase):
    """
    Schema for creating a new warehouse. Inherits from WarehouseBase.
    """

    pass


class WarehouseResponse(WarehouseBase):
    """
    Schema for returning warehouse details in API responses.
    """

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class WarehouseUpdate(BaseModel):
    """
    Schema for updating an existing warehouse. All fields are optional.
    """

    name: Optional[str] = Field(None, min_length=2)
    code: Optional[str] = None
    address: Optional[str] = Field(None, min_length=30)
    status: Optional[WarehouseStatus] = None
