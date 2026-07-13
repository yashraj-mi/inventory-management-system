"""
Dependency injection module for backorder.py.

Provides FastAPI dependencies for backorder components.
"""

from typing import TYPE_CHECKING
from fastapi import Depends

from app.repositories.backorder_repository import BackorderRepository
from app.services.backorder_service import BackorderService
from app.services.sales_order_service import SalesOrderService

if TYPE_CHECKING:
    pass


def get_backorder_repo() -> BackorderRepository:
    """
    Provide a backorder repository instance.

    Returns:
        Repository instance for database operations.
    """
    return BackorderRepository()


def get_backorder_service(
    backorder_repo: BackorderRepository = Depends(get_backorder_repo),
) -> BackorderService:
    """
    Provide a backorder service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    from app.repositories.inventory_repository import InventoryRepository
    from app.repositories.product_repository import ProductRepository
    from app.repositories.warehouse_repository import WarehouseRepository
    from app.services.inventory_transaction_service import InventoryTransactionService
    from app.repositories.inventory_transaction_repository import (
        InventoryTransactionRepository,
    )
    from app.services.inventory_service import InventoryService
    from app.repositories.sales_order_repository import SalesOrderRepository
    from app.repositories.sales_order_item_repository import SalesOrderItemRepository
    from app.services.sales_order_item_service import SalesOrderItemService

    product_repo = ProductRepository()
    warehouse_repo = WarehouseRepository()

    inventory_svc = InventoryService(
        repo=InventoryRepository(),
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
        inventory_transaction_service=InventoryTransactionService(
            repo=InventoryTransactionRepository(),
            product_repo=product_repo,
            warehouse_repo=warehouse_repo,
        ),
        backorder_service=None,  # type: ignore
    )

    soi_service = SalesOrderItemService(
        repo=SalesOrderItemRepository(), product_repo=product_repo
    )

    sales_order_svc = SalesOrderService(
        repo=SalesOrderRepository(),
        warehouse_repo=warehouse_repo,
        soi_service=soi_service,
        inventory_service=inventory_svc,
        backorder_service=None,  # type: ignore
    )

    backorder_svc = BackorderService(
        repo=backorder_repo,
        inventory_service=inventory_svc,
        sales_order_service=sales_order_svc,
    )

    inventory_svc.backorder_service = backorder_svc
    sales_order_svc.backorder_service = backorder_svc

    return backorder_svc
