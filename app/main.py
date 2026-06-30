from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.models.organization import Organization  # noqa: F401
from app.db.models.warehouse import Warehouse  # noqa: F401
from app.db.models.warehouse_users import WarehouseUsers  # noqa: F401
from app.core.database import engine, Base
from app.api.v1.router import api_router

from app.core.error_handlers import init_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.

    Creates all database tables based on SQLAlchemy models on startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(title="Inventory Management System", lifespan=lifespan)

init_error_handlers(app)

app.include_router(api_router)
