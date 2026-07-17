"""Define standard messages for warehouse user assignments.

Provides consistent feedback strings for actions linking or unlinking
staff members and managers to specific warehouse locations.
"""

from enum import Enum


class WarehouseUserMessages(str, Enum):
    """Represent standard messages for warehouse user association operations.

    Used when assigning, removing, or retrieving personnel associated with
    a particular physical warehouse.
    """

    # --- Success Response Messages (Router Layer) ---
    ASSIGNED_SUCCESSFULLY = "User successfully assigned to the warehouse."
    REMOVED_SUCCESSFULLY = "User successfully removed from the warehouse."
    LIST_RETRIEVED = "Successfully retrieved users assigned to the warehouse."

    # --- Error Response Messages (Service Layer) ---
    ALREADY_ASSIGNED = "User is already assigned to this warehouse."

    def format(self, **kwargs) -> str:
        """Inject context variables dynamically into the message string.

        Args:
            **kwargs: Dynamic variables to interpolate into the string.

        Returns:
            str: The formatted message string.
        """
        return self.value.format(**kwargs)
