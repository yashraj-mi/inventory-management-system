"""
warehouse_user_enum.py module.

Provides core functionality and components for the warehouse_user_enum domain.
"""

from enum import Enum


class WarehouseUserMessages(str, Enum):
    # --- Success Response Messages (Router Layer) ---
    """
    Represents the WarehouseUserMessages component.
    """

    ASSIGNED_SUCCESSFULLY = "User successfully assigned to the warehouse."
    REMOVED_SUCCESSFULLY = "User successfully removed from the warehouse."
    LIST_RETRIEVED = "Successfully retrieved users assigned to the warehouse."

    # --- Error Response Messages (Service Layer) ---
    ALREADY_ASSIGNED = "User is already assigned to this warehouse."
    NOT_FOUND = "Assignment mapping record not found."

    # --- Database Transaction Failures ---
    DB_RELATIONAL_CONSTRAINTS = (
        "Cannot remove assignment due to existing relational constraints."
    )
    DB_UNEXPECTED_ASSIGNMENT = (
        "An unexpected database error occurred during warehouse assignment."
    )
    DB_UNEXPECTED_REMOVAL = (
        "An unexpected database error occurred during assignment removal."
    )

    def format(self, **kwargs) -> str:
        """
        Dynamically inject context variables into the enum message string.
        """
        return self.value.format(**kwargs)
