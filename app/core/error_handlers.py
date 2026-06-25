from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppException
from app.schemas.response import StandardResponse


def init_error_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
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
        errors = [
            {"field": err["loc"][-1], "type": err["type"], "msg": err["msg"]}
            for err in exc.errors()
        ]

        response_body = StandardResponse(
            success=False, message="Validation Failed", data=errors
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=response_body.model_dump(),
        )

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        response_body = StandardResponse(
            success=False,
            message="An unexpected internal server error occurred.",
            data=None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_body.model_dump(),
        )
