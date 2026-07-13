"""
router.py module.

Provides core functionality and components for the router domain.
"""

from fastapi import APIRouter
from app.api.v1.endpoints.organization import router as organization_router
from app.api.v1.endpoints.users import router as user_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.warehouse import router as warehouse_router
from app.api.v1.endpoints.warehouse_user import router as warehouse_user_router
from app.api.v1.endpoints.category import router as category_router
from app.api.v1.endpoints.supplier import router as supplier_router
from app.api.v1.endpoints.product import router as product_router
from app.api.v1.endpoints.product_supplier import router as product_supplier_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.customer import router as customer_router
from app.api.v1.endpoints.purchase_order import router as purchase_order_router
from app.api.v1.endpoints.inventory_transaction import (
    router as inventory_transaction_router,
)
from app.api.v1.endpoints.sales_order import router as sales_order_router
from app.api.v1.endpoints.backorder import router as backorder_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(organization_router)

api_router.include_router(user_router)

api_router.include_router(auth_router)

api_router.include_router(warehouse_user_router)

api_router.include_router(warehouse_router)

api_router.include_router(category_router)

api_router.include_router(supplier_router)

api_router.include_router(product_router)

api_router.include_router(product_supplier_router)

api_router.include_router(inventory_router)

api_router.include_router(customer_router)

api_router.include_router(purchase_order_router)

api_router.include_router(inventory_transaction_router)

api_router.include_router(sales_order_router)

api_router.include_router(backorder_router)
