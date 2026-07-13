"""
Dependency injection module for inventory.py.

Provides FastAPI dependencies for inventory components.
"""

from typing import TYPE_CHECKING

from fastapi import Depends

from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository

from app.services.inventory_service import InventoryService
from app.services.inventory_transaction_service import InventoryTransactionService

from app.dependencies.product import get_product_repo
from app.dependencies.warehouse import get_warehouse_repo
from app.dependencies.inventory_transaction import (
    get_inventory_transaction_service,
)

if TYPE_CHECKING:
    pass


def get_inventory_repo() -> InventoryRepository:
    """
    Provide a inventory repository instance.

    Returns:
        Repository instance for database operations.
    """
    return InventoryRepository()


def get_inventory_service(
    inventory_repo: InventoryRepository = Depends(get_inventory_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
    warehouse_repo: WarehouseRepository = Depends(get_warehouse_repo),
    inventory_transaction_service: InventoryTransactionService = Depends(
        get_inventory_transaction_service
    ),
) -> InventoryService:
    """
    Provide a inventory service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    from app.repositories.backorder_repository import BackorderRepository
    from app.services.backorder_service import BackorderService
    from app.repositories.sales_order_repository import SalesOrderRepository
    from app.services.sales_order_service import SalesOrderService
    from app.repositories.sales_order_item_repository import SalesOrderItemRepository
    from app.services.sales_order_item_service import SalesOrderItemService

    inventory_svc = InventoryService(
        repo=inventory_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
        inventory_transaction_service=inventory_transaction_service,
        backorder_service=None,  # type: ignore
    )

    soi_service = SalesOrderItemService(
        repo=SalesOrderItemRepository(),
        # product_repo=product_repo
    )

    sales_order_svc = SalesOrderService(
        repo=SalesOrderRepository(),
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

    return inventory_svc
