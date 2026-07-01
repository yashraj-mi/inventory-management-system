"""
main.py module.

Provides core functionality and components for the main domain.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.models.organization import Organization  # noqa: F401
from app.db.models.warehouse import Warehouse  # noqa: F401
from app.db.models.warehouse_users import WarehouseUsers  # noqa: F401
from app.api.v1.router import api_router

from app.core.error_handlers import init_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.

    Creates all database tables based on SQLAlchemy models on startup.
    """
    # Base.metadata.create_all is now handled by Alembic migrations
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(title="Inventory Management System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_error_handlers(app)

app.include_router(api_router)
