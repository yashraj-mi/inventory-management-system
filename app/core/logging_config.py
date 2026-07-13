"""
Logging configuration module.

Sets up application-wide logging formats, handlers, and filters, ensuring
consistent log output enriched with request-specific context like request IDs.
"""

import logging
import logging.config
import sys

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """
    Configure global logging settings for the application.

    Uses `logging.config.dictConfig` to define custom log formats, attach the
    request ID filter for contextual tracing, and set dynamic log levels based
    on the current environment configuration.

    Side Effects:
        Modifies the global `logging` configuration and handlers.
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)-35s | "
                    "[req:%(request_id)s] | %(message)s"
                ),
                "datefmt": "%H:%M:%S",
            },
        },
        "filters": {
            "request_id": {"()": "app.core.log_context.RequestIDFilter"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_id"],
                "stream": sys.stdout,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn.access": {"level": "WARNING", "propagate": True},
            "httpx": {"level": "WARNING", "propagate": True},
            "sqlalchemy.engine": {
                "level": "INFO" if settings.SQL_ECHO else "WARNING",
                "propagate": True,
            },
        },
    }

    logging.config.dictConfig(logging_config)
