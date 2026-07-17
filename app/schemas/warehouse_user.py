"""
Provide schemas for warehouse staff assignments.

This module contains Pydantic models for managing which users are authorized
to operate within specific warehouse locations.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WarehouseUserAssign(BaseModel):
    """Represent the payload for assigning a user to a warehouse.

    Used in request bodies to grant a staff member operational access to a specific facility.

    Attributes:
        user_id (int): Identifier of the user being assigned.
    """

    user_id: int


class WarehouseUserResponse(BaseModel):
    """Represent a warehouse-user assignment returned in API responses.

    Used to serialize the authorization mapping, including the administrator
    who made the assignment.

    Attributes:
        id (int): Unique identifier of the assignment record.
        warehouse_id (int): Identifier of the assigned warehouse.
        user_id (int): Identifier of the assigned user.
        assigned_by (int): Identifier of the administrator who created the assignment.
        created_at (datetime): Timestamp when the assignment was granted.
    """

    id: int
    warehouse_id: int
    user_id: int
    assigned_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
