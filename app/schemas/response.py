"""
Provide schemas for standardizing API responses.

This module defines generic Pydantic models used to wrap all API responses
in a consistent format, including both standard single-entity responses and
paginated lists.
"""

from typing import Generic, TypeVar, Sequence
from pydantic import BaseModel

# Create a TypeVar to hold the specific schema type for 'data'
T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Represent a generic wrapper to standardize API responses.

    Used across the application to provide a consistent response envelope for
    clients, ensuring every endpoint yields success status and messages.

    Attributes:
        success (bool): Indicates if the API request was successful. Defaults to True.
        message (str): A human-readable message about the result or error.
        data (T | None): The underlying payload returned by the API, typed generically.
    """

    success: bool = True
    message: str
    data: T | None = None


from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedData(BaseModel, Generic[T]):
    """Represent a generic container for paginated API responses.

    Used to wrap lists of results alongside necessary metadata, enabling
    clients to render pagination controls and traverse datasets.

    Attributes:
        items (Sequence[T]): The current page of strongly-typed items.
        total (int): The total number of items available across all pages.
        page (int): The current 1-indexed page number being returned.
        size (int): The maximum number of items requested per page.
        pages (int): The total number of pages available given the total and size.
    """

    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int
