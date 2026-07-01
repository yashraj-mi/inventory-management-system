"""
exceptions.py module.

Provides core functionality and components for the exceptions domain.
"""

from typing import Any


class AppException(Exception):
    """
    Custom exception class for application-level errors.

    Args:
        message (str): The error message.
        status_code (int): The HTTP status code associated with the error.
        data (Any): Optional additional data related to the error.
    """

    def __init__(self, message: str, status_code: int = 400, data: Any = None):
        """
        Executes the __init__ operation.

        Args:
            message: Parameter description.
            status_code: Parameter description.
            data: Parameter description.

        Returns:
            Execution result.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data
