"""
Global exception handlers module.

Registers custom exception handlers with the FastAPI application to ensure
all application errors, validation errors, and unhandled exceptions are
returned in a standardized JSON response format.
"""

from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AppException
from app.schemas.response import StandardResponse
import logging

from app.constants.common_enum import CrudMessages

logger = logging.getLogger(__name__)


def init_error_handlers(app: FastAPI):
    """
    Register global error handlers for the FastAPI application.

    This function attaches custom exception handlers for AppException,
    RequestValidationError, and generic Exception to format API responses.

    Args:
        app (FastAPI): The FastAPI application instance to attach handlers to.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """
        Handle custom application exceptions.

        Formats the response using the status code and message provided in the
        AppException, returning it as a StandardResponse structure.

        Args:
            request (Request): The incoming HTTP request.
            exc (AppException): The raised custom application exception.

        Returns:
            JSONResponse: Formatted JSON response with the provided status code.
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
        Handle request validation errors.

        Catches Pydantic validation errors from FastAPI, parses them into a
        structured list of errors, and returns a 422 Unprocessable Content response.

        Args:
            request (Request): The incoming HTTP request.
            exc (RequestValidationError): The raised validation exception.

        Returns:
            JSONResponse: Formatted JSON response with 422 status and error details.
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

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handle standard HTTP exceptions (e.g., 404 Not Found, 405 Method Not Allowed).

        Wraps standard Starlette/FastAPI HTTPExceptions in the StandardResponse format.
        """
        response_body = StandardResponse(
            success=False, message=str(exc.detail), data=None
        )
        return JSONResponse(
            status_code=exc.status_code, content=response_body.model_dump()
        )

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        """
        Handle all other unhandled exceptions.

        Provides a catch-all mechanism for unexpected server errors, logging the
        full stack trace and returning a generic 500 Internal Server Error response
        to avoid leaking sensitive application state.

        Args:
            request (Request): The incoming HTTP request.
            exc (Exception): The unhandled exception that was raised.

        Returns:
            JSONResponse: Generic 500 JSON response indicating a server error.
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
