"""Define authentication and authorization enumerations.

Provides standardized success and error messages used by the authentication
services and routers to ensure consistent user feedback.
"""

from enum import Enum


class AuthMessages(str, Enum):
    """Represent standard messages for authentication workflows.

    Used by the router and service layers to return consistent text for
    login, token refresh, and permission errors.
    """

    # --- Success Response Messages (Router Layer) ---
    LOGIN_SUCCESSFUL = "Successfully logged in."
    TOKEN_REFRESHED = "Access token refreshed successfully."

    # --- Error Response Messages (Service Layer) ---
    INVALID_CREDENTIALS = "Incorrect email or password."
    INACTIVE_USER = "User account is not active."
    INACTIVE_ORG = "Organization account is not active."
    INVALID_TOKEN = "Invalid token."
    NO_PERMISSION = (
        "Forbidden: You do not have permission to access another organization's\ndata."
    )
    RESOURCE_ACCESS = "You do not have permission to access this resource"
    DB_UNEXPECTED_UPDATE = (
        "An unexpected error occurred while updating the authentication record."
    )

    def format(self, **kwargs) -> str:
        """Inject context variables dynamically into the enum message string.

        Args:
            **kwargs: Arbitrary keyword arguments corresponding to placeholders
                in the message string.

        Returns:
            str: The formatted message string.
        """
        return self.value.format(**kwargs)
