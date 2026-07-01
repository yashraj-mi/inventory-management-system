"""
user_enum.py module.

Provides core functionality and components for the user_enum domain.
"""

from enum import Enum


class UserRole(str, Enum):
    """
    Enum representing the different roles a user can have in the system.
    """

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    WAREHOUSE_MANAGER = "warehouse_manager"
    WAREHOUSE_STAFF = "warehouse_staff"


from enum import Enum


class UserMessages(str, Enum):
    # --- Success Response Messages (Router Layer) ---
    """
    Represents the UserMessages component.
    """

    CREATED_SUCCESSFULLY = "User created successfully."
    LIST_RETRIEVED = "List of all users retrieved successfully."
    ORG_USERS_RETRIEVED = "Successfully retrieved all member accounts provisioned inside organization ID: {organization_id}."
    DETAILS_RETRIEVED = "User details retrieved successfully."
    UPDATED_SUCCESSFULLY = "User updated successfully."
    DELETED_SUCCESSFULLY = "User deleted successfully"

    # --- Error Response Messages (Service Layer) ---
    ALREADY_EXISTS = "User with email '{email}' already exists."
    NOT_FOUND = "User with ID {user_id} not found."
    ORG_NOT_FOUND = "Organization resource verification failed for ID: {org_id}"

    # --- Database Transaction Failures ---
    DB_CONSTRAINT_VIOLATION = (
        "Failed to update user due to a database constraint violation."
    )
    DB_UNEXPECTED_CREATION = (
        "An unexpected database error occurred during user creation."
    )
    DB_UNEXPECTED_UPDATE = "An unexpected database error occurred during user update."
    DB_UNEXPECTED_DELETION = (
        "An unexpected database error occurred during user deletion."
    )
    DB_RELATIONAL_CONSTRAINTS = (
        "Cannot delete user due to existing relational constraints."
    )

    def format(self, **kwargs) -> str:
        """
        Dynamically inject context variables into the enum message string.
        Example: UserMessages.NOT_FOUND.format(user_id=42)
        """
        return self.value.format(**kwargs)
