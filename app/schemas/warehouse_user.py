from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WarehouseUserAssign(BaseModel):
    """
    Schema for assigning a user to a warehouse.
    """

    user_id: int


class WarehouseUserResponse(BaseModel):
    """
    Schema for returning a warehouse user assignment in API responses.
    """

    id: int
    warehouse_id: int
    user_id: int
    assigned_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
