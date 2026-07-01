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

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(organization_router)

api_router.include_router(user_router)

api_router.include_router(auth_router)

api_router.include_router(warehouse_user_router)

api_router.include_router(warehouse_router)
