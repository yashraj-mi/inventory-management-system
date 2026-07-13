"""
Dependency injection module for sales_order_item.py.

Provides FastAPI dependencies for sales_order_item components.
"""

from fastapi import Depends

from app.repositories.sales_order_item_repository import SalesOrderItemRepository
from app.services.sales_order_item_service import SalesOrderItemService


def get_sales_order_item_repo() -> SalesOrderItemRepository:
    """
    Provide a sales_order_item repository instance.

    Returns:
        Repository instance for database operations.
    """
    return SalesOrderItemRepository()


def get_sales_order_item_service(
    sales_order_item_repo: SalesOrderItemRepository = Depends(
        get_sales_order_item_repo
    ),
) -> SalesOrderItemService:
    """
    Provide a sales_order_item service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return SalesOrderItemService(repo=sales_order_item_repo)
