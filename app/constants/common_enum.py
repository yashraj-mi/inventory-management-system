"""Define shared enumerations and generalized messages.

Provides common statuses and CRUD message templates that can be reused
across various modules (e.g., users, products, organizations) to ensure
consistent API responses.
"""

from enum import Enum


class Status(str, Enum):
    """Represent the universal active/inactive state of an entity.

    Used primarily for soft deletes or toggling access for users,
    organizations, and other system components.
    """

    ACTIVE = "active"
    IN_ACTIVE = "in_active"


class CrudMessages(str, Enum):
    """Represent generalized message templates for CRUD operations.

    Used across multiple service layers to generate consistent success
    and error messages by formatting the string with module names and fields.
    """

    # --- Generalized Success Templates ---
    CREATE_SUCCESS = "{module} created successfully."
    READ_ALL_SUCCESS = "List of all {module} retrieved successfully."
    READ_ONE_SUCCESS = "{module} details retrieved successfully."
    UPDATE_SUCCESS = "{module} updated successfully."
    DELETE_SUCCESS = "{module} deleted successfully."
    ORG_DATA_RETRIEVED = "{module} for organization retrieved successfully."
    FETCH_SUCCESS = "{module} fetched successfully."

    # --- Generalized Error Templates ---
    NOT_FOUND = "{module} not found."
    ALREADY_EXISTS = "{module} with this unique identifier already exists."
    ALREADY_EXISTS_FIELD = "{module} with {field} '{value}' already exists."
    ALREADY_IN_USE = "{module} {field} is already in use."
    ORG_NOT_FOUND = "Organization not found."
    ORG_NOT_ACTIVE = "Organization is not active."
    VALIDATION_FAILED = "Validation Failed"

    # --- Generalized DB Failures ---
    DB_CONSTRAINT = "Failed to process {module} due to a database constraint violation."
    DB_RELATIONAL_CONSTRAINT = (
        "Cannot delete {module} due to existing relational constraints."
    )
    DB_UNEXPECTED = "An unexpected database error occurred during {module} {action}."
    INTERNAL_SERVER_ERROR = "An unexpected internal server error occurred."

    def format(self, module: str, **kwargs) -> str:
        """Inject the module name and extra variables into the message template.

        Args:
            module (str): The name of the domain module (e.g., "User", "Product").
            **kwargs: Additional context variables such as ID or field names.

        Returns:
            str: The fully formatted response message.
        """
        return self.value.format(module=module, **kwargs)
