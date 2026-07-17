"""
main.py module.

Provides core functionality and components for the main domain.
"""

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.db.models.organization import Organization  # noqa: F401
from app.db.models.warehouse import Warehouse  # noqa: F401
from app.db.models.warehouse_users import WarehouseUsers  # noqa: F401
from app.api.v1.router import api_router
from app.middlewares.logging_middleware import RequestLoggingMiddleware
from app.core.error_handlers import init_error_handlers
from app.core.redis import init_redis, close_redis
from app.core.logging_config import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.

    Creates all database tables based on SQLAlchemy models on startup.
    """
    # Base.metadata.create_all is now handled by Alembic migrations
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    await init_redis()
    yield
    await close_redis()


app = FastAPI(title="Inventory Management System", lifespan=lifespan)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_error_handlers(app)

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """
    Serve the beautifully designed landing page for the root URL.
    """
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
