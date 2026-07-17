"""
Dependency injection module for purchase_order_item.py.

Provides FastAPI dependencies for purchase_order_item components.
"""

from fastapi import Depends

from app.services.purchase_order_item_service import PurchaseOrderItemService
from app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository


def get_purchase_order_item_repo() -> PurchaseOrderItemRepository:
    """
    Provide a purchase_order_item repository instance.

    Returns:
        Repository instance for database operations.
    """
    return PurchaseOrderItemRepository()


def get_purchase_order_item_service(
    purchase_order_item_repo: PurchaseOrderItemRepository = Depends(
        get_purchase_order_item_repo
    ),
) -> PurchaseOrderItemService:
    """
    Provide a purchase_order_item service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return PurchaseOrderItemService(purchase_order_item_repo)
