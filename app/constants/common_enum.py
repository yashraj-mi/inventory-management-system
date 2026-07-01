"""
common_enum.py module.

Provides core functionality and components for the common_enum domain.
"""

from enum import Enum


class Status(str, Enum):
    """
    Represents the Status component.
    """

    ACTIVE = "active"
    IN_ACTIVE = "in_active"


from enum import Enum


class CrudMessages(str, Enum):
    # --- Generalized Success Templates ---
    """
    Represents the CrudMessages component.
    """

    CREATE_SUCCESS = "{module} created successfully."
    READ_ALL_SUCCESS = "List of all {module}s retrieved successfully."
    READ_ONE_SUCCESS = "{module} details retrieved successfully."
    UPDATE_SUCCESS = "{module} updated successfully."
    DELETE_SUCCESS = "{module} deleted successfully."

    # --- Generalized Error Templates ---
    NOT_FOUND = "{module} with ID {id} not found."
    ALREADY_EXISTS = "{module} with this unique identifier already exists."

    # --- Generalized DB Failures ---
    DB_CONSTRAINT = "Failed to process {module} due to a database constraint violation."
    DB_UNEXPECTED = "An unexpected database error occurred during {module} transaction."

    def format(self, module: str, **kwargs) -> str:
        """
        Automatically injects the module name, plus any extra variables like ID.
        """
        return self.value.format(module=module, **kwargs)
