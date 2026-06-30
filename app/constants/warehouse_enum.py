from enum import Enum


class WarehouseStatus(str, Enum):
    """
    Enum representing the operational status of a warehouse.
    """

    ACTIVE = "active"
    IN_ACTIVE = "in_active"
    ARCHIVED = "archived"
