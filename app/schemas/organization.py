from datetime import datetime
from pydantic import Field, EmailStr, BaseModel, ConfigDict

from app.constants.common_enum import Status


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=15)
    address: str = Field(..., min_length=20, max_length=500)


class OrganizationResponse(BaseModel):
    id: int

    name: str
    email: EmailStr
    phone: str

    address: str

    status: Status

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
