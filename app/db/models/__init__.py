"""
Initialize the database models module.

Provides a centralized import point for all database models to ensure SQLAlchemy
correctly registers them in its Base metadata registry before table creation or migrations.
"""

from app.db.models.backorder import Backorder
from app.db.models.category import Category
from app.db.models.customer import Customer
from app.db.models.inventory import Inventory
from app.db.models.inventory_transaction import InventoryTransaction
from app.db.models.organization import Organization
from app.db.models.product import Product
from app.db.models.product_supplier import ProductSupplier
from app.db.models.purchase_order import PurchaseOrder
from app.db.models.purchase_order_item import PurchaseOrderItem
from app.db.models.sales_order import SalesOrder
from app.db.models.sales_order_item import SalesOrderItem
from app.db.models.supplier import Supplier
from app.db.models.user import User
from app.db.models.warehouse import Warehouse
from app.db.models.warehouse_users import WarehouseUsers

__all__ = [
    "Backorder",
    "Category",
    "Customer",
    "Inventory",
    "InventoryTransaction",
    "Organization",
    "Product",
    "ProductSupplier",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "SalesOrder",
    "SalesOrderItem",
    "Supplier",
    "User",
    "Warehouse",
    "WarehouseUsers",
]
