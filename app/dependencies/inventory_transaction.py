"""
Dependency injection module for inventory_transaction.py.

Provides FastAPI dependencies for inventory_transaction components.
"""

from fastapi import Depends

from app.repositories.inventory_transaction_repository import (
    InventoryTransactionRepository,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.inventory_transaction_service import InventoryTransactionService
from app.dependencies.product import get_product_repo
from app.dependencies.warehouse import get_warehouse_repo


def get_inventory_transaction_repo() -> InventoryTransactionRepository:
    """
    Provide a inventory_transaction repository instance.

    Returns:
        Repository instance for database operations.
    """
    return InventoryTransactionRepository()


def get_inventory_transaction_service(
    inventory_transaction_repo: InventoryTransactionRepository = Depends(
        get_inventory_transaction_repo
    ),
    product_repo: ProductRepository = Depends(get_product_repo),
    warehouse_repo: WarehouseRepository = Depends(get_warehouse_repo),
) -> InventoryTransactionService:
    """
    Provide a inventory_transaction service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return InventoryTransactionService(
        repo=inventory_transaction_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )
