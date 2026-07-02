"""
error_handlers.py module.

Provides core functionality and components for the error_handlers domain.
"""

from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppException
from app.schemas.response import StandardResponse
import logging

from app.constants.common_enum import CrudMessages

logger = logging.getLogger(__name__)


def init_error_handlers(app: FastAPI):
    """
    Executes the init_error_handlers operation.

    Args:
        app: Parameter description.

    Returns:
        Execution result.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """
        Executes the app_exception_handler operation.

        Args:
            request: Parameter description.
            exc: Parameter description.

        Returns:
            Execution result.
        """
        response_body = StandardResponse(
            success=False, message=exc.message, data=exc.data
        )

        return JSONResponse(
            status_code=exc.status_code, content=response_body.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """
        Executes the validation_exception_handler operation.

        Args:
            request: Parameter description.
            exc: Parameter description.

        Returns:
            Execution result.
        """
        errors = [
            {"field": err["loc"][-1], "type": err["type"], "msg": err["msg"]}
            for err in exc.errors()
        ]

        response_body = StandardResponse(
            success=False, message=CrudMessages.VALIDATION_FAILED, data=errors
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=response_body.model_dump(),
        )

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        """
        Executes the universal_exception_handler operation.

        Args:
            request: Parameter description.
            exc: Parameter description.

        Returns:
            Execution result.
        """
        logger.error(
            f"Unhandled Exception on {request.method} {request.url}: {exc}",
            exc_info=True,
        )
        response_body = StandardResponse(
            success=False,
            message=CrudMessages.INTERNAL_SERVER_ERROR,
            data=None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_body.model_dump(),
        )
