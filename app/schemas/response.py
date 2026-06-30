from typing import Generic, TypeVar
from pydantic import BaseModel

# Create a TypeVar to hold the specific schema type for 'data'
T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    A generic wrapper schema to standardize API responses across the application.

    Attributes:
        success (bool): Indicates if the API request was successful. Defaults to True.
        message (str): A human-readable message about the result.
        data (T | None): The generic payload returned by the API, if any.
    """

    success: bool = True
    message: str
    data: T | None = None
