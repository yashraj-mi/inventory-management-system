"""
Dependency injection module for sales_order.py.

Provides FastAPI dependencies for sales_order components.
"""

from typing import TYPE_CHECKING

from fastapi import Depends

from app.repositories.sales_order_repository import SalesOrderRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.sales_order_service import SalesOrderService
from app.dependencies.warehouse import get_warehouse_repo
from app.dependencies.sales_order_item import get_sales_order_item_service
from app.services.sales_order_item_service import SalesOrderItemService
from app.services.inventory_service import InventoryService

if TYPE_CHECKING:
    pass


def get_sales_order_repo() -> SalesOrderRepository:
    """
    Provide a sales_order repository instance.

    Returns:
        Repository instance for database operations.
    """
    return SalesOrderRepository()


def get_sales_order_service(
    sales_order_repo: SalesOrderRepository = Depends(get_sales_order_repo),
    warehouse_repo: WarehouseRepository = Depends(get_warehouse_repo),
    soi_service: SalesOrderItemService = Depends(get_sales_order_item_service),
) -> SalesOrderService:
    """
    Provide a sales_order service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    from app.repositories.inventory_repository import InventoryRepository
    from app.repositories.product_repository import ProductRepository
    from app.services.inventory_transaction_service import InventoryTransactionService
    from app.repositories.inventory_transaction_repository import (
        InventoryTransactionRepository,
    )
    from app.repositories.backorder_repository import BackorderRepository
    from app.services.backorder_service import BackorderService

    product_repo = ProductRepository()

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

    sales_order_svc = SalesOrderService(
        repo=sales_order_repo,
        warehouse_repo=warehouse_repo,
        soi_service=soi_service,
        inventory_service=inventory_svc,
        backorder_service=None,  # type: ignore
    )

    backorder_svc = BackorderService(
        repo=BackorderRepository(),
        inventory_service=inventory_svc,
        sales_order_service=sales_order_svc,
    )

    inventory_svc.backorder_service = backorder_svc
    sales_order_svc.backorder_service = backorder_svc

    return sales_order_svc
