"""Define enumerations for warehouse entities.

Provides statuses indicating a warehouse facility's operational
condition and availability for stock routing within the system.
"""

from enum import Enum


class WarehouseStatus(str, Enum):
    """Represent the operational lifecycle status of a warehouse.

    Controls whether a facility can process inventory transactions (ACTIVE),
    is temporarily disabled (IN_ACTIVE), or permanently closed (ARCHIVED).
    """

    ACTIVE = "active"
    IN_ACTIVE = "in_active"
    ARCHIVED = "archived"


class WarehouseMessages(str, Enum):
    """Represent standard messages for Warehouse operations.

    Currently serves as a placeholder for warehouse-specific feedback
    to maintain consistency across the system.
    """

    pass
