"""
warehouse_enum.py module.

Provides core functionality and components for the warehouse_enum domain.
"""

from enum import Enum


class WarehouseStatus(str, Enum):
    """
    Enum representing the operational status of a warehouse.
    """

    ACTIVE = "active"
    IN_ACTIVE = "in_active"
    ARCHIVED = "archived"


class WarehouseMessages(str, Enum):
    # --- Success Response Messages (Router Layer) ---
    """
    Represents the WarehouseMessages component.
    """

    CREATED_SUCCESSFULLY = "Warehouse created successfully."
    DETAILS_RETRIEVED = "Warehouse details retrieved successfully."
    LIST_RETRIEVED = "List of warehouses retrieved successfully."
    ORG_WAREHOUSES_RETRIEVED = "Warehouses for organization retrieved successfully."
    UPDATED_SUCCESSFULLY = "Warehouse updated successfully."
    DELETED_SUCCESSFULLY = "Warehouse deleted successfully."

    # --- Error Response Messages (Service Layer) ---
    NOT_FOUND = "Warehouse not found."
    ORG_NOT_FOUND = "Organization with id {org_id} not found."
    ORG_NOT_ACTIVE = (
        "Organization with organization id:{org_id} is not currently active."
    )
    CODE_ALREADY_EXISTS = (
        "Warehouse with code '{code}' already exists for this organization."
    )
    CODE_IN_USE = "Warehouse code already in use for this organization."

    # --- Database Transaction Failures ---
    DB_UNEXPECTED_CREATION = (
        "An unexpected database error occurred during warehouse creation."
    )
    DB_CONSTRAINT_UPDATE = (
        "Failed to update warehouse due to a database constraint violation."
    )
    DB_UNEXPECTED_UPDATE = (
        "An unexpected database error occurred during warehouse update."
    )
    DB_RELATIONAL_CONSTRAINTS = (
        "Cannot delete warehouse due to existing relational constraints."
    )
    DB_UNEXPECTED_DELETION = (
        "An unexpected database error occurred during warehouse deletion."
    )

    def format(self, **kwargs) -> str:
        """
        Dynamically inject context variables into the enum message string.
        """
        return self.value.format(**kwargs)
