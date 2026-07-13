"""
Dependency injection module for purchase_order.py.

Provides FastAPI dependencies for purchase_order components.
"""

from fastapi import Depends

from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.purchase_order_service import PurchaseOrderService

from app.dependencies.warehouse import get_warehouse_repo
from app.dependencies.supplier import get_supplier_repo
from app.dependencies.purchase_order_item import get_purchase_order_item_service
from app.services.purchase_order_item_service import PurchaseOrderItemService
from app.dependencies.inventory import get_inventory_service
from app.services.inventory_service import InventoryService


def get_purchase_order_repo() -> PurchaseOrderRepository:
    """
    Provide a purchase_order repository instance.

    Returns:
        Repository instance for database operations.
    """
    return PurchaseOrderRepository()


def get_purchase_order_service(
    purchase_order_repo: PurchaseOrderRepository = Depends(get_purchase_order_repo),
    warehouse_repo: WarehouseRepository = Depends(get_warehouse_repo),
    supplier_repo: SupplierRepository = Depends(get_supplier_repo),
    purchase_order_item_service: PurchaseOrderItemService = Depends(
        get_purchase_order_item_service
    ),
    inventory_service: InventoryService = Depends(get_inventory_service),
) -> PurchaseOrderService:
    """
    Provide a purchase_order service instance.

    Args:
        Dependencies injected by FastAPI.

    Returns:
        Service instance for business logic.
    """
    return PurchaseOrderService(
        repo=purchase_order_repo,
        warehouse_repo=warehouse_repo,
        supplier_repo=supplier_repo,
        poi_service=purchase_order_item_service,
        inventory_service=inventory_service,
    )
