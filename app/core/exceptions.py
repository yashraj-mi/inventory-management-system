"""
Custom exception definitions module.

Provides standardized exception classes used throughout the application to signal
expected business logic errors or validation failures, ensuring consistent error responses.
"""

from typing import Any
from fastapi import status


class AppException(Exception):
    """
    Custom exception class for application-level errors.

    Used to raise controlled errors that are caught by the global error handler
    and returned as structured JSON responses.

    Attributes:
        message (str): The specific error message to be returned to the client.
        status_code (int): The HTTP status code associated with the error.
        data (Any): Optional additional data or context related to the error.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None,
    ):
        """
        Initialize the AppException.

        Args:
            message (str): A descriptive error message explaining the failure.
            status_code (int, optional): The HTTP status code to return. Defaults to 400.
            data (Any, optional): Supplementary data related to the error context. Defaults to None.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data
