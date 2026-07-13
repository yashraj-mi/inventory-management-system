"""
Dependency injection module for pagination.py.

Provides FastAPI dependencies for pagination components.
"""

from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    Represents pagination parameters for a paginated query.

    This model holds the current page number and page size,
    and provides a computed `offset` property used to translate
    page-based pagination into SQL's OFFSET/LIMIT pagination.

    Example:
        params = PaginationParams(page=2, size=5)
        params.offset  # → 5 (skips the first 5 rows)
    """

    page: int = Field(..., description="The current page number (1-indexed).")
    size: int = Field(..., description="Number of items to return per page.")

    @property
    def offset(self) -> int:
        """
        Calculates the number of rows to skip based on the current
        page and page size.

        Formula:
            offset = (page - 1) * size

        Example:
            page=1, size=10 → offset=0   (first page, skip nothing)
            page=2, size=10 → offset=10  (second page, skip first 10 rows)
            page=3, size=5  → offset=10  (third page, skip first 10 rows)

        Returns:
            int: The number of rows to skip before starting to
                 collect the result set (used as SQL OFFSET).
        """
        return (self.page - 1) * self.size


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """
    FastAPI dependency that extracts and validates pagination
    query parameters from the incoming request, then wraps them
    into a `PaginationParams` instance.

    Query Parameters:
        page (int): The page number to retrieve. Must be >= 1.
                    Defaults to 1 (first page).
        size (int): Number of items per page. Must be between
                    1 and 100 inclusive. Defaults to 10.

    Usage:
        @router.get("/items")
        async def list_items(
            params: PaginationParams = Depends(get_pagination_params),
        ):
            ...

    Example Request:
        GET /items?page=2&size=20
        → PaginationParams(page=2, size=20)

    Returns:
        PaginationParams: A validated pagination params object,
                           ready to be passed into `paginate_query()`.
    """
    return PaginationParams(page=page, size=size)
