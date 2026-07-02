"""
auth_enum.py module.

Provides core functionality and components for the auth_enum domain.
"""

from enum import Enum


class AuthMessages(str, Enum):
    # --- Success Response Messages (Router Layer) ---
    """
    Represents the AuthMessages component.
    """

    LOGIN_SUCCESSFUL = "Successfully logged in."
    TOKEN_REFRESHED = "Access token refreshed successfully."

    # --- Error Response Messages (Service Layer) ---
    INVALID_CREDENTIALS = "Incorrect email or password."
    INACTIVE_USER = "User account is not active."
    INACTIVE_ORG = "Organization account is not active."
    INVALID_TOKEN = "Invalid token."
    NO_PERMISSION = (
        "Forbidden: You do not have permission to access another organization's data."
    )
    RESOURCE_ACCESS = "You do not have permission to access this resource"
    DB_UNEXPECTED_UPDATE = (
        "An unexpected error occurred while updating the authentication record."
    )

    def format(self, **kwargs) -> str:
        """
        Dynamically inject context variables into the enum message string.
        Example: AuthMessages.INACTIVE_USER.format()
        """
        return self.value.format(**kwargs)
